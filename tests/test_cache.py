"""Tests for audit caching system."""
import pytest
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from llm_council.cache import AuditCache, CacheKey


class TestCacheKey:
    """Test cache key generation."""
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        key1 = CacheKey.generate("gpt-4o", "template_hash", "prompt_hash", "content_hash")
        key2 = CacheKey.generate("gpt-4o", "template_hash", "prompt_hash", "content_hash")
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) > 10  # Should be a meaningful hash
    
    def test_cache_key_different_inputs(self):
        """Test that different inputs generate different cache keys."""
        key1 = CacheKey.generate("gpt-4o", "template1", "prompt1", "content1")
        key2 = CacheKey.generate("gpt-4o", "template2", "prompt1", "content1")
        key3 = CacheKey.generate("gpt-3.5-turbo", "template1", "prompt1", "content1")
        
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
    
    def test_cache_key_hash_components(self):
        """Test that cache key includes all components."""
        template_content = "Template content"
        prompt_content = "Prompt content"
        document_content = "Document content"
        
        key = CacheKey.generate_from_content("gpt-4o", template_content, prompt_content, document_content)
        
        assert isinstance(key, str)
        # Should be deterministic
        key2 = CacheKey.generate_from_content("gpt-4o", template_content, prompt_content, document_content)
        assert key == key2


class TestAuditCache:
    """Test audit cache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization with different backends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AuditCache(cache_dir=cache_dir)
            
            assert cache.cache_dir == cache_dir
            assert cache.cache_dir.exists()
    
    def test_cache_hit_miss(self):
        """Test basic cache hit and miss functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AuditCache(cache_dir=cache_dir)
            
            cache_key = "test_key_123"
            test_data = {"auditor_role": "pm", "score": 4.5}
            
            # Cache miss
            result = cache.get(cache_key)
            assert result is None
            
            # Store in cache
            cache.set(cache_key, test_data)
            
            # Cache hit
            result = cache.get(cache_key)
            assert result == test_data
    
    def test_cache_expiry(self):
        """Test cache expiry functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            # Set very short expiry for testing
            cache = AuditCache(cache_dir=cache_dir, expiry_hours=0.001)  # ~3.6 seconds
            
            cache_key = "expiry_test_key"
            test_data = {"auditor_role": "pm", "score": 4.0}
            
            # Store data
            cache.set(cache_key, test_data)
            
            # Should be available immediately
            assert cache.get(cache_key) == test_data
            
            # Should expire after very short time (simulate by manually checking)
            import time
            time.sleep(4)  # Wait longer than expiry
            
            # Should be None after expiry
            assert cache.get(cache_key) is None
    
    def test_cache_serialization(self):
        """Test that complex objects are properly serialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AuditCache(cache_dir=cache_dir)
            
            complex_data = {
                "auditor_role": "security",
                "scores_detailed": {
                    "simplicity": {"score": 4, "pass": True, "justification": "Clear requirements"},
                    "actionability": {"score": 3, "pass": True, "justification": "Actionable items"}
                },
                "blocking_issues": [
                    {"severity": "high", "description": "Security gap", "impact": "Data breach risk"}
                ],
                "nested_arrays": [["a", "b"], ["c", "d"]]
            }
            
            cache_key = "complex_data_key"
            cache.set(cache_key, complex_data)
            
            retrieved = cache.get(cache_key)
            assert retrieved == complex_data
            assert retrieved["auditor_role"] == "security"
            assert retrieved["scores_detailed"]["simplicity"]["score"] == 4
            assert len(retrieved["blocking_issues"]) == 1
    
    def test_cache_file_storage(self):
        """Test that cache creates and manages files properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AuditCache(cache_dir=cache_dir)
            
            cache_key = "file_test_key"
            test_data = {"test": "data"}
            
            cache.set(cache_key, test_data)
            
            # Check that cache file was created
            cache_files = list(cache_dir.glob("*.json"))
            assert len(cache_files) > 0
            
            # Check file content is valid JSON
            cache_file = cache_files[0]
            with open(cache_file, 'r') as f:
                stored_data = json.load(f)
            
            assert "data" in stored_data
            assert "timestamp" in stored_data
    
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir)
            cache = AuditCache(cache_dir=cache_dir)
            
            # Add some data
            cache.set("key1", {"data": "test1"})
            cache.set("key2", {"data": "test2"})
            
            # Verify data exists
            assert cache.get("key1") is not None
            assert cache.get("key2") is not None
            
            # Clear cache
            cache.clear()
            
            # Verify data is gone
            assert cache.get("key1") is None
            assert cache.get("key2") is None


class TestCacheIntegration:
    """Test cache integration with orchestrator."""
    
    @patch('llm_council.orchestrator.AsyncOpenAI')
    def test_auditor_worker_cache_integration(self, mock_openai):
        """Test that AuditorWorker uses cache when available."""
        # This test will verify cache integration after implementation
        pass
    
    def test_cache_cost_tracking(self):
        """Test that cache reduces actual costs."""
        # This test will verify cost reduction after implementation  
        pass