"""Tests for ConsensusEngine thresholds and behavior."""
from llm_council.consensus import ConsensusEngine


def make_response(role: str, avg: float, overall_pass: bool = True, blocking=None):
    return {
        'auditor_role': role,
        'overall_assessment': {
            'average_score': avg,
            'overall_pass': overall_pass,
        },
        'blocking_issues': blocking or [],
    }


def test_consensus_passes_when_above_thresholds():
    engine = ConsensusEngine(score_threshold=3.8, approval_threshold=0.67)
    responses = [
        make_response('pm', 4.0, True),
        make_response('security', 3.9, True),
        make_response('data', 4.1, True),
    ]
    result = engine.calculate_consensus(responses)
    assert result.final_decision == 'PASS'
    assert result.consensus_pass is True
    assert result.approval_pass is True


def test_consensus_fails_low_score_or_approvals():
    engine = ConsensusEngine(score_threshold=3.8, approval_threshold=0.67)
    # Low average score
    responses_low = [
        make_response('pm', 3.0, True),
        make_response('security', 3.2, True),
        make_response('data', 3.1, True),
    ]
    res1 = engine.calculate_consensus(responses_low)
    assert res1.final_decision == 'FAIL'
    assert res1.consensus_pass is False

    # Low approval rate
    responses_approvals = [
        make_response('pm', 4.0, True),
        make_response('security', 4.0, False),
        make_response('data', 4.0, False),
    ]
    res2 = engine.calculate_consensus(responses_approvals)
    assert res2.final_decision == 'FAIL'
    assert res2.approval_pass is False


def test_blocking_issues_trigger_fail():
    engine = ConsensusEngine(blocking_gates={'critical': 0, 'high': 1, 'medium': 5, 'low': 99})
    responses = [
        make_response('pm', 4.2, True, blocking=[{'severity': 'high'}]),
        make_response('security', 4.1, True, blocking=[{'severity': 'high'}]),
        make_response('data', 4.3, True),
    ]
    res = engine.calculate_consensus(responses)
    assert res.final_decision == 'FAIL'
    assert any('Too many high issues' in r for r in res.failure_reasons)
