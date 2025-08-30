"""Tests for ResearchAgent integration (R-PRD-010)."""
import asyncio
from src.llm_council.research_agent import ResearchAgent, ResearchContext


def test_research_agent_disabled_returns_empty():
    """Test that a disabled research agent returns an empty context."""
    agent = ResearchAgent(provider='tavily', enabled=False)
    ctx = asyncio.run(agent.gather_context('Any content', stage='vision'))
    assert isinstance(ctx, ResearchContext)
    assert ctx.market_trends == []
    assert ctx.competitors == []
    assert ctx.technical_insights == []


def test_research_agent_enabled_uses_fallback_and_formats():
    """Test that an enabled research agent uses fallback data and formats it."""
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