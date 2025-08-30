"""Tests for council member debate and interaction system."""
import pytest
from unittest.mock import Mock, patch

from council_members import CouncilMember, Council, DebateRound, DebateResult


class TestCouncilMember:
    """Test individual council member functionality."""
    def test_council_member_creation(self):
        """Test creating council members with different roles and models."""
        pm_member = CouncilMember(
            role="pm",
            model_provider="openai",
            model_name="gpt-4o",
            expertise_areas=["business_logic", "user_needs", "market_validation"],
            personality="analytical_optimistic"
        )

        assert pm_member.role == "pm"
        assert pm_member.model_provider == "openai"
        assert "business_logic" in pm_member.expertise_areas
        assert pm_member.personality == "analytical_optimistic"

    def test_council_member_with_debate_style(self):
        """Test that council members have distinct debate styles."""
        security_member = CouncilMember(
            role="security",
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            expertise_areas=["threat_modeling", "data_privacy", "compliance"],
            personality="cautious_thorough",
            debate_style="devil_advocate"
        )

        assert security_member.debate_style == "devil_advocate"
        assert "threat_modeling" in security_member.expertise_areas
        assert security_member.personality == "cautious_thorough"


class TestCouncilDebate:
    """Test council debate and consensus building."""

    @pytest.mark.asyncio
    @patch('council_members.acompletion')
    async def test_council_member_initial_review(self, mock_completion):
        """Test that council member can provide initial document review."""
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content='{"auditor_role": "pm", "overall_assessment": {"summary": "Strong vision but needs metrics"}}'))]
        )

        pm_member = CouncilMember(
            role="pm",
            model_provider="openai",
            model_name="gpt-4o",
            expertise_areas=["business_logic"]
        )

        document = "# Vision\nBuild AI document review platform"
        review = await pm_member.provide_initial_review(document, "vision")

        assert review["auditor_role"] == "pm"
        assert "summary" in review["overall_assessment"]
        mock_completion.assert_called_once()

    @pytest.mark.asyncio
    @patch('council_members.acompletion')
    async def test_council_member_respond_to_peer(self, mock_completion):
        """Test that council member can respond to another member's feedback."""
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content='{"questions": ["How do we measure success?"], "agreements": ["Security is critical"], "counterpoints": ["Cost may be higher"]}'))]
        )

        pm_member = CouncilMember(role="pm", model_provider="openai", model_name="gpt-4o")

        peer_feedback = {
            "auditor_role": "security",
            "overall_assessment": {"summary": "Document lacks security considerations"}
        }

        response = await pm_member.respond_to_peer_feedback([peer_feedback], "vision", "vision")

        assert "questions" in response
        assert "agreements" in response
        assert "counterpoints" in response

    @pytest.mark.asyncio
    async def test_council_debate_rounds(self):
        """Test that council can conduct multiple debate rounds."""
        council = Council()

        # Add diverse council members
        council.add_member(CouncilMember("pm", "openai", "gpt-4o"))
        council.add_member(CouncilMember("security", "anthropic", "claude-3-5-sonnet-20241022"))
        council.add_member(CouncilMember("data_eval", "google", "gemini-1.5-pro"))

        document = "# Vision\nBuild AI audit platform with multi-LLM consensus"

        with patch.object(council, '_execute_debate_round') as mock_round:
            mock_round.return_value = DebateRound(
                round_number=1,
                initial_reviews={},
                peer_responses={},
                emerging_consensus=["Need clearer success metrics"],
                remaining_disagreements=["Cost vs quality tradeoff"]
            )

            debate_result = await council.conduct_debate(document, "vision", max_rounds=3)

            assert isinstance(debate_result, DebateResult)
            assert debate_result.total_rounds >= 1
            assert len(debate_result.participating_members) == 3


class TestCouncilConsensusBuilding:
    """Test consensus building through iterative debate."""

    def test_consensus_emergence_detection(self):
        """Test that council can detect when consensus is emerging."""
        from council_members import analyze_consensus_emergence

        debate_rounds = [
            DebateRound(
                round_number=1,
                initial_reviews={"pm": {"summary": "Good vision"}, "security": {"summary": "Needs security"}},
                peer_responses={},
                emerging_consensus=["Document quality is important"],
                remaining_disagreements=["Cost vs security tradeoff", "Timeline concerns"]
            ),
            DebateRound(
                round_number=2,
                initial_reviews={},
                peer_responses={"pm": {"agreements": ["Security is critical"]}, "security": {"agreements": ["Cost efficiency matters"]}},
                emerging_consensus=["Document quality is important", "Security is critical", "Cost efficiency matters"],
                remaining_disagreements=["Timeline concerns"]
            )
        ]

        consensus_analysis = analyze_consensus_emergence(debate_rounds)

        assert consensus_analysis.convergence_trend > 0  # Getting more consensus
        assert len(consensus_analysis.stable_agreements) >= 1
        assert len(consensus_analysis.unresolved_disagreements) == 1

    def test_question_generation_for_alignment(self):
        """Test that council members generate concrete questions for alignment."""
        from council_members import generate_alignment_questions

        disagreements = [
            "PM wants fast delivery, Security wants thorough analysis",
            "Data team needs evaluation framework, Infrastructure wants simple implementation"
        ]

        questions = generate_alignment_questions(disagreements)

        assert len(questions) >= 2
        assert any(("delivery" in q.lower() or "deliver" in q.lower()) and "analysis" in q.lower() for q in questions)
        assert any("evaluation" in q.lower() and ("implementation" in q.lower() or "implement" in q.lower()) for q in questions)

    def test_debate_termination_conditions(self):
        """Test that debate terminates appropriately."""
        from council_members import should_continue_debate

        # High consensus should terminate debate
        high_consensus_round = DebateRound(
            round_number=2,
            initial_reviews={},
            peer_responses={},
            emerging_consensus=["A", "B", "C", "D", "E"],  # 5 agreements
            remaining_disagreements=["Minor concern"]      # 1 disagreement
        )

        assert not should_continue_debate([high_consensus_round], max_rounds=5)

        # Low consensus should continue debate
        low_consensus_round = DebateRound(
            round_number=1,
            initial_reviews={},
            peer_responses={},
            emerging_consensus=["A"],                       # 1 agreement
            remaining_disagreements=["B", "C", "D", "E"]   # 4 disagreements
        )

        assert should_continue_debate([low_consensus_round], max_rounds=5)
