"""
Tests for ResearchAgent integration (R-PRD-010).

VERIFIES: REQ-010 (research agent integration for context gathering)
VALIDATES: External API integration and research context formatting
USE_CASE: UC-002 (automated context expansion and market research)
INTERFACES: research_agent.py (ResearchAgent, ResearchContext)
LAST_SYNC: 2025-08-30
"""
import asyncio
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm_council.research_agent import ResearchAgent, ResearchContext


def test_research_agent_disabled_returns_empty():
    """
    Test that a disabled research agent returns an empty context.
    
    VERIFIES: REQ-010 (research agent configuration and fallback behavior)
    VALIDATES: Graceful degradation when research is disabled
    USE_CASE: UC-002 (offline or cost-controlled operation mode)
    """
    agent = ResearchAgent(provider='tavily', enabled=False)
    ctx = asyncio.run(agent.gather_context('Any content', stage='vision'))
    assert isinstance(ctx, ResearchContext)
    assert ctx.market_trends == []
    assert ctx.competitors == []
    assert ctx.technical_insights == []


def test_research_agent_enabled_uses_fallback_and_formats():
    """
    Test that an enabled research agent uses fallback data and formats it.
    
    VERIFIES: REQ-010 (research integration with external APIs)
    VALIDATES: ResearchContext data structure and document formatting
    USE_CASE: UC-002 (automated context enhancement for documents)
    """
    # Provide a dummy API key so provider init does not fail
    agent = ResearchAgent(provider='tavily', api_key='test-key', enabled=True)
    content = 'AI document review CLI vision'
    ctx = asyncio.run(agent.gather_context(content, stage='vision'))

    # Fallback path returns some structured results
    assert isinstance(ctx, ResearchContext)
    assert ctx.query_used
    assert isinstance(ctx.sources, list)

    enhanced = agent.format_context_for_document(ctx, '# Vision\nBody')
    assert 'Research Context' in enhanced
    assert 'Market' in enhanced or 'Competitive' in enhanced or 'Technical' in enhanced
