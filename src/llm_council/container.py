"""Dependency injection container following industry standards.

Implements a proper DI container using the dependency-injector pattern
for clean architecture and testability. All dependencies are registered
here and can be easily swapped for testing or different implementations.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Type, TypeVar, Optional, List
import logging

from .interfaces import (
    IAuditorProvider,
    IConsensusEngine,
    IAlignmentValidator,
    IResearchProvider,
    ICacheService,
    IDocumentLoader,
    INotificationService,
    IMetricsCollector,
    IConfigurationProvider,
    IEventPublisher,
    IEventSubscriber,
    IAuditorProviderFactory,
)

T = TypeVar('T')

logger = logging.getLogger(__name__)


class DIContainer:
    """Dependency injection container for managing service instances."""
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}
        self._initialized = False
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton instance."""
        self._singletons[interface] = implementation
        logger.debug(f"Registered singleton: {interface.__name__} -> {implementation.__class__.__name__}")
    
    def register_transient(self, interface: Type[T], factory: callable) -> None:
        """Register a transient service with a factory function."""
        self._factories[interface] = factory
        logger.debug(f"Registered transient: {interface.__name__} -> {factory.__name__}")
    
    def register_scoped(self, interface: Type[T], implementation: T) -> None:
        """Register a scoped service (one per request/operation)."""
        self._services[interface] = implementation
        logger.debug(f"Registered scoped: {interface.__name__} -> {implementation.__class__.__name__}")
    
    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service by its interface type."""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]
        
        # Check scoped services
        if interface in self._services:
            return self._services[interface]
        
        # Check factories for transient services
        if interface in self._factories:
            return self._factories[interface]()
        
        raise ValueError(f"Service not registered: {interface.__name__}")
    
    def resolve_optional(self, interface: Type[T]) -> Optional[T]:
        """Resolve a service optionally, returning None if not found."""
        try:
            return self.resolve(interface)
        except ValueError:
            return None
    
    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._initialized = False
        logger.info("DI Container cleared")
    
    def is_registered(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return (interface in self._singletons or 
                interface in self._services or 
                interface in self._factories)


# Configuration implementations
class EnvironmentConfigurationProvider:
    """Configuration provider that reads from environment variables and config files."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file and environment."""
        # Load from file if provided
        if self.config_file and self.config_file.exists():
            import yaml
            with open(self.config_file, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        
        # Override with environment variables
        env_vars = {
            'OPENAI_API_KEY': 'api_keys.openai',
            'ANTHROPIC_API_KEY': 'api_keys.anthropic', 
            'GOOGLE_API_KEY': 'api_keys.google',
            'TAVILY_API_KEY': 'api_keys.tavily',
            'DEBUG': 'debug',
            'CACHE_TTL': 'cache.ttl',
            'MAX_PARALLEL_AUDITORS': 'orchestration.max_parallel',
        }
        
        for env_var, config_path in env_vars.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested_value(config_path, value)
    
    def _set_nested_value(self, path: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        keys = path.split('.')
        current = self._config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section."""
        return self.get_config(section, {})
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._load_config()


# Service implementations
class InMemoryCacheService:
    """Simple in-memory cache implementation."""
    
    def __init__(self, default_ttl: int = 3600):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._default_ttl = default_ttl
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        import time
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL."""
        import time
        ttl = ttl or self._default_ttl
        expiry = time.time() + ttl if ttl > 0 else None
        self._cache[key] = (value, expiry)
    
    async def clear(self, pattern: Optional[str] = None) -> None:
        """Clear cache entries, optionally by pattern."""
        if pattern is None:
            self._cache.clear()
        else:
            import re
            regex = re.compile(pattern)
            keys_to_delete = [k for k in self._cache.keys() if regex.search(k)]
            for key in keys_to_delete:
                del self._cache[key]


class SimpleMetricsCollector:
    """Simple metrics collector implementation."""
    
    def __init__(self):
        self._metrics: Dict[str, List[Any]] = {
            'audit_durations': [],
            'costs': [],
            'token_usage': [],
            'errors': []
        }
    
    def record_audit_duration(self, duration: float, stage: str, provider: str) -> None:
        """Record audit execution duration."""
        self._metrics['audit_durations'].append({
            'duration': duration,
            'stage': stage,
            'provider': provider,
            'timestamp': import time.time() if 'time' in globals() else 0
        })
    
    def record_cost(self, cost: float, provider: str, tokens_used: int) -> None:
        """Record cost and token usage."""
        import time
        self._metrics['costs'].append({
            'cost': cost,
            'provider': provider,
            'tokens': tokens_used,
            'timestamp': time.time()
        })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        return {
            'total_audits': len(self._metrics['audit_durations']),
            'total_cost': sum(m['cost'] for m in self._metrics['costs']),
            'avg_duration': sum(m['duration'] for m in self._metrics['audit_durations']) / 
                           max(len(self._metrics['audit_durations']), 1),
            'total_tokens': sum(m['tokens'] for m in self._metrics['costs'])
        }


class EventBus:
    """Simple event bus for pub/sub messaging."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[callable]] = {}
        self._next_id = 0
        self._subscriptions: Dict[str, tuple] = {}  # subscription_id -> (event_type, handler)
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to all subscribers."""
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def subscribe(self, event_type: str, handler: callable) -> str:
        """Subscribe to event type and return subscription ID."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        
        subscription_id = f"sub_{self._next_id}"
        self._next_id += 1
        self._subscriptions[subscription_id] = (event_type, handler)
        
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from events."""
        if subscription_id in self._subscriptions:
            event_type, handler = self._subscriptions[subscription_id]
            if event_type in self._subscribers:
                self._subscribers[event_type].remove(handler)
            del self._subscriptions[subscription_id]


# Global container instance
container = DIContainer()


def configure_container(config_file: Optional[Path] = None) -> DIContainer:
    """Configure the DI container with default implementations."""
    if container._initialized:
        return container
    
    logger.info("Configuring dependency injection container")
    
    # Configuration
    config_provider = EnvironmentConfigurationProvider(config_file)
    container.register_singleton(IConfigurationProvider, config_provider)
    
    # Cache service
    cache_ttl = config_provider.get_config('cache.ttl', 3600)
    cache_service = InMemoryCacheService(cache_ttl)
    container.register_singleton(ICacheService, cache_service)
    
    # Metrics collector
    metrics_collector = SimpleMetricsCollector()
    container.register_singleton(IMetricsCollector, metrics_collector)
    
    # Event bus
    event_bus = EventBus()
    container.register_singleton(IEventPublisher, event_bus)
    container.register_singleton(IEventSubscriber, event_bus)
    
    container._initialized = True
    logger.info("DI Container configured successfully")
    
    return container


def get_container() -> DIContainer:
    """Get the global DI container instance."""
    if not container._initialized:
        return configure_container()
    return container


# Decorators for dependency injection
def inject(interface: Type[T]) -> callable:
    """Decorator to inject dependencies into functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            service = container.resolve(interface)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "DIContainer",
    "EnvironmentConfigurationProvider",
    "InMemoryCacheService", 
    "SimpleMetricsCollector",
    "EventBus",
    "container",
    "configure_container",
    "get_container",
    "inject"
]