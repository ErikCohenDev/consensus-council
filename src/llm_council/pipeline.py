"""Multi-stage pipeline orchestration across document stages.

Coordinates stage audits (Vision → PRD → Architecture), aggregates results,
checks cross-document alignment, and supports iterative gating with optional
revision strategies.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Iterable

from .orchestrator import AuditorOrchestrator, OrchestrationResult
from .alignment import AlignmentValidator, AlignmentResult


DEFAULT_STAGES: List[str] = ["vision", "prd", "architecture"]


@dataclass
class StageResult:
    stage: str
    orchestration: OrchestrationResult


@dataclass
class PipelineSummary:
    success: bool
    stage_results: Dict[str, StageResult]
    alignment_results: List[AlignmentResult]
    iterations: int


class RevisionStrategy:
    """Hook for proposing content revisions based on results.

    Default implementation is a no-op. A concrete strategy could, for example,
    call a synthesis agent to update documents based on misalignments and
    auditor feedback.
    """

    def propose_revisions(
        self,
        documents: Dict[str, str],
        stage_results: Dict[str, StageResult],
        alignment_results: List[AlignmentResult],
    ) -> Dict[str, str]:
        return {}


class PipelineOrchestrator:
    """Runs a multi-stage gated pipeline with alignment checks and iteration."""

    def __init__(
        self,
        template_path: Path,
        model: str,
        api_key: str,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
        max_parallel: int = 4,
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
    ):
        self._template_path = template_path
        self._model = model
        self._api_key = api_key
        self._cache_dir = cache_dir
        self._enable_cache = enable_cache
        self._max_parallel = max_parallel
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries

        self._alignment = AlignmentValidator()

    def _make_orchestrator(self) -> AuditorOrchestrator:
        return AuditorOrchestrator(
            template_path=self._template_path,
            model=self._model,
            api_key=self._api_key,
            max_parallel=self._max_parallel,
            timeout_seconds=self._timeout_seconds,
            max_retries=self._max_retries,
            cache_dir=self._cache_dir,
            enable_cache=self._enable_cache,
        )

    async def _audit_stage(
        self, orchestrator: AuditorOrchestrator, stage: str, content: str
    ) -> OrchestrationResult:
        return await orchestrator.execute_stage_audit(stage, content)

    def run(
        self,
        documents: Dict[str, str],
        stages: Optional[Iterable[str]] = None,
        max_iterations: int = 1,
        revision_strategy: Optional[RevisionStrategy] = None,
        output_dir: Optional[Path] = None,
    ) -> PipelineSummary:
        stages = list(stages or DEFAULT_STAGES)
        stage_results: Dict[str, StageResult] = {}
        revision_strategy = revision_strategy or RevisionStrategy()

        iterations = 0
        while iterations < max_iterations:
            iterations += 1
            orchestrator = self._make_orchestrator()

            # Run audits per stage in sequence (could be parallelized by group)
            for stage in stages:
                content = documents.get(stage, "")
                result = asyncio.run(self._audit_stage(orchestrator, stage, content))
                stage_results[stage] = StageResult(stage=stage, orchestration=result)

            # Cross-document alignment (full chain)
            alignment_results = self._alignment.validate_document_chain(documents)

            # Check gating conditions
            all_stages_pass = all(
                (sr.orchestration.consensus_result is not None)
                and (sr.orchestration.consensus_result.final_decision == "PASS")
                for sr in stage_results.values()
            )
            all_aligned = all(ar.is_aligned for ar in alignment_results)
            success = all_stages_pass and all_aligned

            # Optional output drop (per-iteration snapshot)
            if output_dir:
                self._write_iteration_outputs(output_dir, iterations, stage_results, alignment_results)

            if success:
                return PipelineSummary(
                    success=True,
                    stage_results=stage_results,
                    alignment_results=alignment_results,
                    iterations=iterations,
                )

            # Ask strategy for revisions; if none, stop early
            proposed = revision_strategy.propose_revisions(documents, stage_results, alignment_results)
            if not proposed:
                # Still return summary so caller can inspect failures
                return PipelineSummary(
                    success=False,
                    stage_results=stage_results,
                    alignment_results=alignment_results,
                    iterations=iterations,
                )

            # Apply proposals and continue loop
            documents.update(proposed)

        # Max iterations reached
        alignment_results = self._alignment.validate_document_chain(documents)
        return PipelineSummary(
            success=False,
            stage_results=stage_results,
            alignment_results=alignment_results,
            iterations=iterations,
        )

    def _write_iteration_outputs(
        self,
        output_dir: Path,
        iteration: int,
        stage_results: Dict[str, StageResult],
        alignment_results: List[AlignmentResult],
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Stage summaries
        for stage, sr in stage_results.items():
            orc = sr.orchestration
            lines: List[str] = []
            lines.append(f"=== AUDIT SUMMARY (iter {iteration}) - {stage.upper()} ===")
            if orc.consensus_result:
                cr = orc.consensus_result
                lines.append(f"Final Decision: {cr.final_decision}")
                lines.append(
                    f"Weighted Consensus Score: {cr.weighted_average:.1f} (Agreement {cr.agreement_level:.2f})"
                )
            else:
                lines.append("Final Decision: UNKNOWN (partial failure)")

            (output_dir / f"audit_{stage}_iter{iteration}.md").write_text("\n".join(lines), encoding="utf-8")

        # Alignment snapshot
        lines = [f"=== ALIGNMENT SNAPSHOT (iter {iteration}) ==="]
        for ar in alignment_results:
            status = "✅ ALIGNED" if ar.is_aligned else "❌ MISALIGNED"
            lines.append(f"{ar.source_stage} → {ar.target_stage}: {status} ({ar.alignment_score:.1f}/5)")
            if not ar.is_aligned and ar.misalignments:
                lines.append(f"  Issue: {ar.misalignments[0]}")
        (output_dir / f"alignment_iter{iteration}.md").write_text("\n".join(lines), encoding="utf-8")


__all__ = [
    "PipelineOrchestrator",
    "PipelineSummary",
    "StageResult",
    "RevisionStrategy",
]

