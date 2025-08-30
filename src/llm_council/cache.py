"""Audit response caching system."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional


class CacheKey:
    """Generates consistent cache keys for audit responses."""

    @staticmethod
    def generate(model: str, template_hash: str, prompt_hash: str, content_hash: str) -> str:
        """Generate cache key from components."""
        combined = f"{model}:{template_hash}:{prompt_hash}:{content_hash}"
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    @staticmethod
    def generate_from_content(model: str, template_content: str, prompt_content: str, document_content: str) -> str:
        """Generate cache key from actual content."""
        template_hash = hashlib.sha256(template_content.encode()).hexdigest()[:16]
        prompt_hash = hashlib.sha256(prompt_content.encode()).hexdigest()[:16]
        content_hash = hashlib.sha256(document_content.encode()).hexdigest()[:16]

        return CacheKey.generate(model, template_hash, prompt_hash, content_hash)


class AuditCache:
    """File-based cache for audit responses."""

    def __init__(self, cache_dir: Path, expiry_hours: float = 4.0):
        """Initialize cache with directory and expiry time."""
        self.cache_dir = cache_dir
        self.expiry_hours = expiry_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached data if available and not expired."""
        cache_file = self._get_cache_file_path(cache_key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check expiry
            stored_timestamp = cache_data.get("timestamp", 0)
            current_time = time.time()
            expiry_seconds = self.expiry_hours * 3600

            if current_time - stored_timestamp > expiry_seconds:
                # Remove expired file
                cache_file.unlink(missing_ok=True)
                return None

            return cache_data.get("data")

        except (json.JSONDecodeError, KeyError, OSError):
            # Remove corrupted cache file
            cache_file.unlink(missing_ok=True)
            return None

    def set(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store data in cache with timestamp."""
        cache_file = self._get_cache_file_path(cache_key)

        cache_data = {
            "timestamp": time.time(),
            "data": data
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except OSError:
            # Silently fail if unable to write cache
            pass

    def clear(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
            except OSError:
                pass

    def cleanup_expired(self) -> int:
        """Remove expired cache files and return count removed."""
        current_time = time.time()
        expiry_seconds = self.expiry_hours * 3600
        removed_count = 0

        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                stored_timestamp = cache_data.get("timestamp", 0)

                if current_time - stored_timestamp > expiry_seconds:
                    cache_file.unlink()
                    removed_count += 1

            except (json.JSONDecodeError, KeyError, OSError):
                # Remove corrupted files
                cache_file.unlink(missing_ok=True)
                removed_count += 1

        return removed_count


__all__ = ["CacheKey", "AuditCache"]
