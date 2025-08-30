"""Tests for orchestrator retry/timeout behavior and global call cap."""
import asyncio
import json
from pathlib import Path
import pytest

from llm_council.orchestrator import AuditorOrchestrator


class StubChoice:
    def __init__(self, content: str):
        self.message = type('M', (), {'content': content})


class StubResponse:
    def __init__(self, content: str):
        self.choices = [StubChoice(content)]


class TimeoutThenSuccessClient:
    """Client that times out on first call, then succeeds subsequently."""
    def __init__(self, json_payload: dict):
        self._payload = json_payload
        self._calls = 0
        self.chat = self
        self.completions = self

    async def create(self, *args, **kwargs):
        self._calls += 1
        if self._calls % 2 == 1:
            # First call fails
            await asyncio.sleep(0)
            raise asyncio.TimeoutError()
        return StubResponse(json.dumps(self._payload))


class AlwaysSuccessClient:
    def __init__(self, json_payload: dict):
        self._payload = json_payload
        self.chat = self
        self.completions = self

    async def create(self, *args, **kwargs):
        await asyncio.sleep(0)
        return StubResponse(json.dumps(self._payload))


@pytest.mark.asyncio
async def test_retry_then_success(monkeypatch, tmp_path: Path):
    # Patch TemplateEngine methods to avoid real files
    from llm_council import orchestrator as orch_mod
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_stage_auditors', lambda self, stage: ['pm'])
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_auditor_prompt', lambda self, stage, role, doc: 'prompt')
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_template_content', lambda self: 'template')

    payload = {
        'auditor_role': 'pm',
        'overall_assessment': { 'overall_pass': True, 'average_score': 4.0 },
        'blocking_issues': [],
    }

    tpl = tmp_path / 'template.yaml'
    tpl.write_text('project_info: {name: t, description: t, stages: [vision]}')
    orch = AuditorOrchestrator(template_path=tpl, model='gpt-4o', api_key='k', max_retries=2)
    # Inject our timeout-then-success client
    orch._client = TimeoutThenSuccessClient(payload)

    result = await orch.execute_stage_audit('vision', 'doc')
    assert result.success is True
    assert result.consensus_result is not None


@pytest.mark.asyncio
async def test_global_call_cap(monkeypatch, tmp_path: Path):
    # Two auditors but cap at 1 total call → one will fail
    from llm_council import orchestrator as orch_mod
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_stage_auditors', lambda self, stage: ['pm', 'security'])
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_auditor_prompt', lambda self, stage, role, doc: 'prompt')
    monkeypatch.setattr(orch_mod.TemplateEngine, 'get_template_content', lambda self: 'template')

    payload = {
        'auditor_role': 'pm',
        'overall_assessment': { 'overall_pass': True, 'average_score': 4.2 },
        'blocking_issues': [],
    }

    tpl = tmp_path / 'template.yaml'
    tpl.write_text('project_info: {name: t, description: t, stages: [vision]}')
    orch = AuditorOrchestrator(
        template_path=tpl,
        model='gpt-4o',
        api_key='k',
        max_retries=1,
        max_calls_total=1,
    )
    orch._client = AlwaysSuccessClient(payload)

    result = await orch.execute_stage_audit('vision', 'doc')
    assert result.success is False
    assert len(result.failed_auditors) >= 1

