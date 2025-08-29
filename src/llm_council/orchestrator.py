"""Auditor orchestration module.

Provides async execution of multiple LLM "auditors" and aggregates their
responses into an orchestration result (and optional consensus result).

The implementation here is intentionally lightweight – it focuses on the
interfaces expected by the test suite (AuditorWorker, AuditorOrchestrator,
OrchestrationResult, AuditorExecutionError) and defers advanced behaviors
like adaptive retry backoff, cost aggregation, streaming, and human review
escalation to future iterations.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI  # Patched in tests

from .consensus import ConsensusEngine, ConsensusResult
from .templates import TemplateEngine
from .cache import AuditCache, CacheKey


class AuditorExecutionError(Exception):
    """Raised when an individual auditor fails permanently."""


@dataclass
class OrchestrationResult:
    """Aggregate result of executing all auditors for a stage."""

    success: bool
    auditor_responses: List[Dict[str, Any]]
    failed_auditors: List[str]
    consensus_result: Optional[ConsensusResult]
    execution_time: float
    total_tokens: Optional[int] = None
    total_cost: Optional[float] = None


class AuditorWorker:
    """Executes a single auditor LLM call with retry + timeout + JSON validation."""

    def __init__(
        self,
        role: str,
        stage: str,
        client: AsyncOpenAI,
        timeout: float = 60.0,
        max_retries: int = 3,
        model: str = "gpt-4o",
        cache: Optional[AuditCache] = None,
    ):
        self.role = role
        self.stage = stage
        self.client = client
        self.timeout = timeout
        self.max_retries = max_retries
        self.model = model
        self.cache = cache

    async def execute_audit(self, prompt: str, template_content: str = "", document_content: str = "") -> Dict[str, Any]:
        """Execute the audit prompt and return parsed JSON.

        Retries on invalid JSON or generic exceptions up to max_retries.
        Raises AuditorExecutionError when retries are exhausted.
        Uses caching if available to reduce costs and API calls.
        """
        # Check cache if available
        if self.cache:
            cache_key = CacheKey.generate_from_content(self.model, template_content, prompt, document_content)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result

        last_err: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are an expert structured auditor. Return ONLY valid JSON that conforms to the requested schema.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        temperature=0.2,
                    ),
                    timeout=self.timeout,
                )

                content = response.choices[0].message.content if response.choices else ""
                # Parse JSON
                data = json.loads(content or "{}")
                # Basic schema sanity checks (role + stage presence)
                if not isinstance(data, dict) or "auditor_role" not in data:
                    raise ValueError("Missing auditor_role in response JSON")

                # Store in cache if available
                if self.cache:
                    cache_key = CacheKey.generate_from_content(self.model, template_content, prompt, document_content)
                    self.cache.set(cache_key, data)

                return data
            except (json.JSONDecodeError, ValueError, asyncio.TimeoutError, Exception) as err:  # noqa: BLE001
                last_err = err
                if attempt == self.max_retries:
                    break
                # Small adaptive delay before retry (could be exponential later)
                await asyncio.sleep(0.1 * attempt)

        raise AuditorExecutionError(
            f"Auditor {self.role} failed after {self.max_retries} attempts: {last_err}"
        )


class AuditorOrchestrator:
    """Coordinates execution of multiple auditor workers for a given stage."""

    def __init__(
        self,
        template_path: Path,
        model: str,
        api_key: str,
        max_parallel: int = 4,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
    ):
        self.template_path = template_path
        self.model = model
        self.api_key = api_key
        self.max_parallel = max_parallel
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.enable_cache = enable_cache

        self._template_engine = TemplateEngine(template_path)
        self._client = AsyncOpenAI(api_key=api_key)

        # Initialize cache if enabled
        if enable_cache and cache_dir:
            self._cache = AuditCache(cache_dir)
        else:
            self._cache = None

    async def execute_stage_audit(
        self, stage: str, document_content: str
    ) -> OrchestrationResult:
        start = time.perf_counter()
        auditors = self._template_engine.get_stage_auditors(stage)
        if not auditors:
            # No auditors defined – treat as failure requiring configuration
            duration = time.perf_counter() - start
            return OrchestrationResult(
                success=False,
                auditor_responses=[],
                failed_auditors=[],
                consensus_result=None,
                execution_time=duration,
            )

        semaphore = asyncio.Semaphore(self.max_parallel)
        responses: List[Dict[str, Any]] = []
        failed: List[str] = []

        async def run_auditor(role: str):
            prompt = self._template_engine.get_auditor_prompt(
                stage, role, document_content
            )
            template_content = self._template_engine.get_template_content() if self._cache else ""
            worker = AuditorWorker(
                role=role,
                stage=stage,
                client=self._client,
                timeout=self.timeout_seconds,
                max_retries=self.max_retries,
                model=self.model,
                cache=self._cache,
            )
            async with semaphore:
                try:
                    result = await worker.execute_audit(prompt, template_content, document_content)
                    responses.append(result)
                except AuditorExecutionError:
                    failed.append(role)

        await asyncio.gather(*(run_auditor(role) for role in auditors))

        # Determine success; only compute consensus if all auditors succeeded
        if failed:
            duration = time.perf_counter() - start
            return OrchestrationResult(
                success=False,
                auditor_responses=responses,
                failed_auditors=failed,
                consensus_result=None,
                execution_time=duration,
            )

        consensus_engine = ConsensusEngine()
        consensus_result = consensus_engine.calculate_consensus(responses)
        duration = time.perf_counter() - start
        return OrchestrationResult(
            success=True,
            auditor_responses=responses,
            failed_auditors=[],
            consensus_result=consensus_result,
            execution_time=duration,
        )


__all__ = [
    "AuditorWorker",
    "AuditorOrchestrator",
    "AuditorExecutionError",
    "OrchestrationResult",
]
