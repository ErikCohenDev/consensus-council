"""Audit service handling audit orchestration and execution.

This service is responsible for coordinating audits while maintaining
separation of concerns and following the single responsibility principle.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from ..interfaces import (
    IAuditorProvider,
    IConsensusEngine,
    ICacheService,
    IMetricsCollector,
    IEventPublisher
)
from ..schemas import AuditorResponse


logger = logging.getLogger(__name__)


@dataclass
class AuditRequest:
    """Request object for audit operations."""
    stage: str
    content: str
    requester_id: str
    priority: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AuditResult:
    """Result of audit operation."""
    request_id: str
    stage: str
    success: bool
    auditor_responses: List[AuditorResponse]
    consensus_result: Optional[Dict[str, Any]]
    execution_time: float
    cost_estimate: float
    error_message: Optional[str] = None


class AuditService:
    """Service for handling audit operations with proper separation of concerns."""
    
    def __init__(
        self,
        auditor_providers: List[IAuditorProvider],
        consensus_engine: IConsensusEngine,
        cache_service: ICacheService,
        metrics_collector: IMetricsCollector,
        event_publisher: IEventPublisher,
        max_parallel: int = 4,
        timeout_seconds: float = 60.0
    ):
        self._auditor_providers = auditor_providers
        self._consensus_engine = consensus_engine
        self._cache_service = cache_service
        self._metrics_collector = metrics_collector
        self._event_publisher = event_publisher
        self._max_parallel = max_parallel
        self._timeout_seconds = timeout_seconds
        
        logger.info(f"AuditService initialized with {len(auditor_providers)} providers")
    
    async def execute_audit(self, request: AuditRequest) -> AuditResult:
        """Execute audit for the given request."""
        start_time = time.perf_counter()
        request_id = self._generate_request_id(request)
        
        logger.info(f"Starting audit for stage '{request.stage}' (request_id: {request_id})")
        
        try:
            # Publish audit started event
            await self._event_publisher.publish("audit_started", {
                "request_id": request_id,
                "stage": request.stage,
                "timestamp": time.time()
            })
            
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self._cache_service.get(cache_key)
            
            if cached_result:
                logger.info(f"Cache hit for request {request_id}")
                await self._event_publisher.publish("audit_cache_hit", {
                    "request_id": request_id,
                    "cache_key": cache_key
                })
                return cached_result
            
            # Execute audit with providers
            auditor_responses = await self._execute_parallel_audits(request)
            
            # Calculate consensus
            consensus_result = None
            if auditor_responses:
                consensus_result = self._consensus_engine.calculate_consensus(auditor_responses)
            
            execution_time = time.perf_counter() - start_time
            
            # Create result
            result = AuditResult(
                request_id=request_id,
                stage=request.stage,
                success=bool(auditor_responses and consensus_result),
                auditor_responses=auditor_responses,
                consensus_result=consensus_result,
                execution_time=execution_time,
                cost_estimate=self._estimate_cost(auditor_responses)
            )
            
            # Cache successful results
            if result.success:
                await self._cache_service.set(cache_key, result, ttl=3600)
            
            # Record metrics
            for provider in self._auditor_providers:
                self._metrics_collector.record_audit_duration(
                    execution_time / len(self._auditor_providers),
                    request.stage,
                    provider.provider_name
                )
            
            self._metrics_collector.record_cost(
                result.cost_estimate,
                "ensemble", 
                sum(len(resp.blocking_issues) for resp in auditor_responses)
            )
            
            # Publish completion event
            await self._event_publisher.publish("audit_completed", {
                "request_id": request_id,
                "success": result.success,
                "execution_time": execution_time,
                "cost": result.cost_estimate
            })
            
            logger.info(f"Audit completed for request {request_id} in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            error_msg = str(e)
            
            logger.error(f"Audit failed for request {request_id}: {error_msg}")
            
            # Publish error event
            await self._event_publisher.publish("audit_failed", {
                "request_id": request_id,
                "error": error_msg,
                "execution_time": execution_time
            })
            
            return AuditResult(
                request_id=request_id,
                stage=request.stage,
                success=False,
                auditor_responses=[],
                consensus_result=None,
                execution_time=execution_time,
                cost_estimate=0.0,
                error_message=error_msg
            )
    
    async def _execute_parallel_audits(self, request: AuditRequest) -> List[AuditorResponse]:
        """Execute audits in parallel with the configured providers."""
        semaphore = asyncio.Semaphore(self._max_parallel)
        
        async def execute_single_audit(provider: IAuditorProvider) -> Optional[AuditorResponse]:
            async with semaphore:
                try:
                    # Create stage-specific prompt
                    prompt = self._create_audit_prompt(request, provider)
                    
                    # Execute with timeout
                    response = await asyncio.wait_for(
                        provider.execute_audit(prompt, request.stage),
                        timeout=self._timeout_seconds
                    )
                    
                    logger.debug(f"Audit completed for provider {provider.provider_name}")
                    return response
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Audit timeout for provider {provider.provider_name}")
                    return None
                except Exception as e:
                    logger.error(f"Audit error for provider {provider.provider_name}: {e}")
                    return None
        
        # Execute all audits in parallel
        tasks = [execute_single_audit(provider) for provider in self._auditor_providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful responses
        successful_responses = [
            result for result in results 
            if isinstance(result, AuditorResponse)
        ]
        
        logger.info(f"Completed {len(successful_responses)}/{len(self._auditor_providers)} audits")
        return successful_responses
    
    def _create_audit_prompt(self, request: AuditRequest, provider: IAuditorProvider) -> str:
        """Create audit prompt tailored for the specific provider and stage."""
        base_prompt = f"""
        Audit this {request.stage} document from your perspective as an expert reviewer.
        
        Document content:
        {request.content}
        
        Please provide structured feedback focusing on:
        - Quality and completeness
        - Potential risks and issues
        - Specific improvements needed
        - Overall assessment and recommendation
        
        Respond with valid JSON following the expected schema.
        """
        
        # Add provider-specific context
        if hasattr(provider, 'get_role_context'):
            role_context = provider.get_role_context()
            base_prompt += f"\n\nFocus areas for your role: {role_context}"
        
        return base_prompt.strip()
    
    def _generate_request_id(self, request: AuditRequest) -> str:
        """Generate unique request ID."""
        import hashlib
        content = f"{request.stage}:{request.content[:100]}:{request.requester_id}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _generate_cache_key(self, request: AuditRequest) -> str:
        """Generate cache key for the request."""
        import hashlib
        
        provider_names = sorted(p.provider_name for p in self._auditor_providers)
        content = f"{request.stage}:{request.content}:{':'.join(provider_names)}"
        
        return f"audit:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    
    def _estimate_cost(self, responses: List[AuditorResponse]) -> float:
        """Estimate cost based on the audit responses."""
        # Simple cost estimation - replace with actual cost calculation
        base_cost_per_audit = 0.01  # $0.01 per audit
        complexity_multiplier = sum(len(resp.blocking_issues) for resp in responses) * 0.001
        
        return len(responses) * base_cost_per_audit + complexity_multiplier
    
    async def get_audit_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an audit request."""
        # In a real implementation, this would check a status store
        # For now, return basic status information
        return {
            "request_id": request_id,
            "status": "unknown",
            "message": "Status tracking not yet implemented"
        }
    
    async def cancel_audit(self, request_id: str) -> bool:
        """Cancel a running audit request."""
        # Implementation would depend on the specific orchestration mechanism
        logger.info(f"Cancel requested for audit {request_id}")
        return False  # Not implemented yet
    
    def get_supported_stages(self) -> List[str]:
        """Get list of supported audit stages."""
        return [
            "research_brief",
            "market_scan", 
            "vision",
            "prd",
            "architecture",
            "implementation_plan"
        ]
    
    def get_provider_info(self) -> List[Dict[str, str]]:
        """Get information about configured audit providers."""
        return [
            {
                "provider_name": provider.provider_name,
                "model_name": provider.model_name
            }
            for provider in self._auditor_providers
        ]


__all__ = ["AuditService", "AuditRequest", "AuditResult"]