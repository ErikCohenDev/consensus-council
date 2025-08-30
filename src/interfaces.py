"""Interface definitions following SOLID principles.

This module defines all the interfaces and protocols that components
in the system must implement, enabling proper dependency injection
and making the system easily testable and extensible.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Any, Protocol
from pathlib import Path

from schemas import AuditorResponse


class IAuditorProvider(Protocol):
    """Interface for audit providers (different LLM implementations)."""

    async def execute_audit(self, prompt: str, stage: str) -> AuditorResponse:
        """Execute audit and return structured response."""

    @property
    def provider_name(self) -> str:
        """Get the provider name (e.g., 'openai', 'anthropic')."""

    @property
    def model_name(self) -> str:
        """Get the specific model name."""


class IConsensusEngine(Protocol):
    """Interface for consensus calculation algorithms."""

    def calculate_consensus(
        self,
        responses: List[AuditorResponse],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate consensus from multiple auditor responses."""

    def get_algorithm_name(self) -> str:
        """Get the name of the consensus algorithm."""


class IAlignmentValidator(Protocol):
    """Interface for document alignment validation."""

    def validate_alignment(
        self,
        source_content: str,
        target_content: str,
        source_stage: str,
        target_stage: str
    ) -> Dict[str, Any]:
        """Validate alignment between two documents."""


class IResearchProvider(Protocol):
    """Interface for research and context gathering."""

    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for information and return structured results."""

    @property
    def provider_name(self) -> str:
        """Get the research provider name."""


class ICacheService(Protocol):
    """Interface for caching services."""

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL."""

    async def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries, optionally by pattern."""


class IDocumentLoader(Protocol):
    """Interface for document loading strategies."""

    def load_documents(self, docs_path: Path) -> Dict[str, str]:
        """Load documents from the specified path."""

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""


class INotificationService(Protocol):
    """Interface for real-time notifications and updates."""

    async def notify_status_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send notification about status changes."""

    async def notify_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Send error notification."""


class IMetricsCollector(Protocol):
    """Interface for collecting performance and usage metrics."""

    def record_audit_duration(self, duration: float, stage: str, provider: str) -> None:
        """Record audit execution duration."""

    def record_cost(self, cost: float, provider: str, tokens_used: int) -> None:
        """Record cost and token usage."""

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""


# Abstract base classes for core components

class BaseAuditOrchestrator(ABC):
    """Base class for audit orchestrators."""

    def __init__(
        self,
        auditor_provider: IAuditorProvider,
        consensus_engine: IConsensusEngine,
        cache_service: ICacheService,
        metrics_collector: IMetricsCollector
    ):
        self.auditor_provider = auditor_provider
        self.consensus_engine = consensus_engine
        self.cache_service = cache_service
        self.metrics_collector = metrics_collector

    @abstractmethod
    async def execute_audit(self, stage: str, content: str) -> Dict[str, Any]:
        """Execute audit for a given stage and content."""


class BaseCouncilMember(ABC):
    """Base class for council members with pluggable providers."""

    def __init__(
        self,
        role: str,
        auditor_provider: IAuditorProvider,
        expertise_areas: List[str],
        personality: str = "balanced"
    ):
        self.role = role
        self.auditor_provider = auditor_provider
        self.expertise_areas = expertise_areas
        self.personality = personality

    @abstractmethod
    async def provide_review(self, document: str, stage: str) -> Dict[str, Any]:
        """Provide review of the document."""

    @abstractmethod
    async def respond_to_peers(
        self,
        peer_reviews: List[Dict[str, Any]],
        document: str,
        stage: str
    ) -> Dict[str, Any]:
        """Respond to peer feedback."""


class BaseUIService(ABC):
    """Base class for UI services handling different aspects of the interface."""

    @abstractmethod
    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle UI events and return appropriate responses."""

    @abstractmethod
    def get_service_name(self) -> str:
        """Get the service name for identification."""


# Configuration interfaces

class IConfigurationProvider(Protocol):
    """Interface for configuration providers."""

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""

    def reload(self) -> None:
        """Reload configuration from source."""


# Event system interfaces

class IEventPublisher(Protocol):
    """Interface for event publishing."""

    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event."""


class IEventSubscriber(Protocol):
    """Interface for event subscription."""

    async def subscribe(
        self,
        event_type: str,
        handler: Callable
    ) -> str:
        """Subscribe to event type and return subscription ID."""

    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""


# Factory interfaces

class IAuditorProviderFactory(Protocol):
    """Factory for creating auditor providers."""

    def create_provider(
        self,
        provider_type: str,
        model_name: str,
        config: Dict[str, Any]
    ) -> IAuditorProvider:
        """Create auditor provider instance."""

    def get_supported_providers(self) -> List[str]:
        """Get list of supported provider types."""


__all__ = [
    # Core interfaces
    "IAuditorProvider",
    "IConsensusEngine",
    "IAlignmentValidator",
    "IResearchProvider",
    "ICacheService",
    "IDocumentLoader",
    "INotificationService",
    "IMetricsCollector",

    # Base classes
    "BaseAuditOrchestrator",
    "BaseCouncilMember",
    "BaseUIService",

    # Configuration
    "IConfigurationProvider",

    # Event system
    "IEventPublisher",
    "IEventSubscriber",

    # Factories
    "IAuditorProviderFactory",
]
