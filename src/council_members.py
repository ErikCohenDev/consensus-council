"""Council member debate and interaction system.

Implements sophisticated council member objects that can debate documents,
respond to peer feedback, ask clarifying questions, and build consensus
through iterative discussion rounds.
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    from litellm import acompletion
except ImportError:
    acompletion = None


class DebateStyle(Enum):
    """Different debate styles for council members."""
    COLLABORATIVE = "collaborative"
    DEVIL_ADVOCATE = "devil_advocate"
    ANALYTICAL = "analytical"
    PRAGMATIC = "pragmatic"
    CREATIVE = "creative"


@dataclass
class DebateRound:
    """Results from a single round of council debate."""
    round_number: int
    initial_reviews: Dict[str, Dict[str, Any]]
    peer_responses: Dict[str, Dict[str, Any]]
    emerging_consensus: List[str]
    remaining_disagreements: List[str]
    questions_raised: List[str] = field(default_factory=list)
    execution_time: float = 0.0


@dataclass
class DebateResult:
    """Final result of council debate process."""
    success: bool
    total_rounds: int
    participating_members: List[str]
    final_consensus: List[str]
    unresolved_disagreements: List[str]
    key_insights_by_member: Dict[str, List[str]]
    consensus_score: float
    debate_rounds: List[DebateRound]


@dataclass
class ConsensusAnalysis:
    """Analysis of consensus emergence across debate rounds."""
    convergence_trend: float  # -1 to 1, positive = converging
    stable_agreements: List[str]
    unresolved_disagreements: List[str]
    confidence_level: float


class CouncilMember:
    """Individual council member that can debate and respond to peers."""

    def __init__(
        self,
        role: str,
        model_provider: str,
        model_name: str,
        expertise_areas: List[str] = None,
        personality: str = "balanced",
        debate_style: str = "collaborative",
        api_key: Optional[str] = None
    ):
        self.role = role
        self.model_provider = model_provider
        self.model_name = model_name
        self.expertise_areas = expertise_areas or []
        self.personality = personality
        self.debate_style = debate_style
        self.api_key = api_key

        # Ensure LiteLLM is available
        if acompletion is None:
            raise ImportError("litellm package required for council member functionality")

    async def provide_initial_review(self, document: str, stage: str) -> Dict[str, Any]:
        """Provide initial review of document from this member's perspective."""
        model_name = f"{self.model_provider}/{self.model_name}"
        if self.model_provider == "openrouter":
            model_name = self.model_name

        prompt = f"""As an expert {self.role} with {self.personality} personality, provide a structured audit of this {stage} document.

Focus areas: {', '.join(self.expertise_areas)}
Debate style: {self.debate_style}

Document:
{document}

Return JSON with:
- auditor_role: "{self.role}"
- overall_assessment: {{summary, overall_pass, average_score, top_risks, quick_wins}}
- expertise_focus: specific insights from your {self.role} perspective
- debate_readiness: questions you want to ask other council members"""

        response = await acompletion(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {self.role} council member with {self.debate_style} debate style. Provide structured JSON feedback."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content if response.choices else "{}"
        data = json.loads(content)

        # Add member metadata
        data["council_member_id"] = f"{self.role}_{self.model_provider}"
        data["model_provider"] = self.model_provider
        data["debate_style"] = self.debate_style

        return data

    async def respond_to_peer_feedback(self, peer_reviews: List[Dict[str, Any]], document: str, stage: str) -> Dict[str, Any]:
        """Respond to other council members' feedback and ask clarifying questions."""
        model_name = f"{self.model_provider}/{self.model_name}"
        if self.model_provider == "openrouter":
            model_name = self.model_name

        peer_summaries = []
        for review in peer_reviews:
            role = review.get("auditor_role", "unknown")
            summary = review.get("overall_assessment", {}).get("summary", "No summary")
            risks = review.get("overall_assessment", {}).get("top_risks", [])
            peer_summaries.append(f"{role}: {summary} | Risks: {', '.join(risks[:2])}")

        prompt = f"""As {self.role} council member, respond to your peers' feedback on this {stage} document.

Your expertise: {', '.join(self.expertise_areas)}
Your style: {self.debate_style}

Peer feedback:
{chr(10).join(peer_summaries)}

Document:
{document}

Respond with JSON containing:
- questions: specific questions to ask peers for clarification
- agreements: points where you agree with peers
- counterpoints: respectful disagreements with reasoning
- synthesis_proposals: suggestions to reconcile different viewpoints
- updated_assessment: any changes to your initial review based on peer input"""

        response = await acompletion(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {self.role} council member engaging in constructive debate. Ask concrete questions and find common ground."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4  # Slightly higher for creative debate
        )

        content = response.choices[0].message.content if response.choices else "{}"
        return json.loads(content)

    def __repr__(self) -> str:
        return f"CouncilMember(role={self.role}, provider={self.model_provider}, style={self.debate_style})"


class Council:
    """Council that orchestrates debate between multiple members."""

    def __init__(self, max_debate_rounds: int = 3):
        self.members: List[CouncilMember] = []
        self.max_debate_rounds = max_debate_rounds

    def add_member(self, member: CouncilMember) -> None:
        """Add a member to the council."""
        self.members.append(member)

    def get_member_by_role(self, role: str) -> Optional[CouncilMember]:
        """Get council member by role."""
        return next((m for m in self.members if m.role == role), None)

    async def conduct_debate(self, document: str, stage: str, max_rounds: Optional[int] = None) -> DebateResult:
        """Conduct multi-round debate until consensus or max rounds reached."""
        max_rounds = max_rounds or self.max_debate_rounds
        debate_rounds = []

        # Round 1: Initial reviews from all members
        round_1 = await self._execute_initial_round(document, stage)
        debate_rounds.append(round_1)

        # Subsequent rounds: Peer responses and consensus building
        for round_num in range(2, max_rounds + 1):
            if not should_continue_debate(debate_rounds, max_rounds):
                break

            debate_round = await self._execute_debate_round(document, stage, round_num, debate_rounds)
            debate_rounds.append(debate_round)

        # Analyze final consensus
        consensus_analysis = analyze_consensus_emergence(debate_rounds)

        return DebateResult(
            success=consensus_analysis.confidence_level >= 0.7,
            total_rounds=len(debate_rounds),
            participating_members=[m.role for m in self.members],
            final_consensus=consensus_analysis.stable_agreements,
            unresolved_disagreements=consensus_analysis.unresolved_disagreements,
            key_insights_by_member=self._extract_member_insights(debate_rounds),
            consensus_score=consensus_analysis.confidence_level,
            debate_rounds=debate_rounds
        )

    async def _execute_initial_round(self, document: str, stage: str) -> DebateRound:
        """Execute initial review round where each member provides independent feedback."""
        start_time = time.perf_counter()

        # Get initial reviews from all members in parallel
        tasks = [member.provide_initial_review(document, stage) for member in self.members]
        initial_reviews_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert to dict keyed by role
        initial_reviews = {}
        for i, review in enumerate(initial_reviews_list):
            if isinstance(review, dict):
                role = self.members[i].role
                initial_reviews[role] = review

        execution_time = time.perf_counter() - start_time

        return DebateRound(
            round_number=1,
            initial_reviews=initial_reviews,
            peer_responses={},
            emerging_consensus=self._extract_emerging_consensus(initial_reviews),
            remaining_disagreements=self._extract_disagreements(initial_reviews),
            execution_time=execution_time
        )

    async def _execute_debate_round(self, document: str, stage: str, round_num: int, previous_rounds: List[DebateRound]) -> DebateRound:
        """Execute a debate round where members respond to each other."""
        start_time = time.perf_counter()

        # Get all previous reviews for context
        all_previous_reviews = []
        for round_data in previous_rounds:
            all_previous_reviews.extend(round_data.initial_reviews.values())

        # Each member responds to peer feedback
        tasks = []
        for member in self.members:
            # Get peer reviews (excluding their own)
            peer_reviews = [r for r in all_previous_reviews if r.get("auditor_role") != member.role]
            tasks.append(member.respond_to_peer_feedback(peer_reviews, document, stage))

        peer_responses_list = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert to dict keyed by role
        peer_responses = {}
        for i, response in enumerate(peer_responses_list):
            if isinstance(response, dict):
                role = self.members[i].role
                peer_responses[role] = response

        execution_time = time.perf_counter() - start_time

        return DebateRound(
            round_number=round_num,
            initial_reviews={},
            peer_responses=peer_responses,
            emerging_consensus=self._extract_consensus_from_responses(peer_responses),
            remaining_disagreements=self._extract_disagreements_from_responses(peer_responses),
            execution_time=execution_time
        )

    def _extract_emerging_consensus(self, reviews: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract points of emerging consensus from initial reviews."""
        # Simple implementation - look for common themes in summaries
        consensus_points = []

        summaries = [review.get("overall_assessment", {}).get("summary", "") for review in reviews.values()]

        # Look for common keywords/themes
        common_themes = ["security", "performance", "cost", "user", "quality", "scalability"]
        for theme in common_themes:
            if sum(1 for summary in summaries if theme in summary.lower()) >= 2:
                consensus_points.append(f"Multiple members emphasize {theme} importance")

        return consensus_points[:5]  # Limit to top 5

    def _extract_disagreements(self, reviews: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract disagreements from initial reviews."""
        disagreements = []

        # Compare pass/fail decisions
        pass_decisions = [review.get("overall_assessment", {}).get("overall_pass", False) for review in reviews.values()]
        if not all(pass_decisions) and any(pass_decisions):
            disagreements.append("Council members disagree on overall pass/fail decision")

        # Compare top risks
        all_risks = []
        for review in reviews.values():
            risks = review.get("overall_assessment", {}).get("top_risks", [])
            all_risks.extend(risks)

        if len(set(all_risks)) > len(all_risks) * 0.5:  # High risk diversity
            disagreements.append("Significant disagreement on risk prioritization")

        return disagreements

    def _extract_consensus_from_responses(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract consensus points from peer responses."""
        consensus_points = []

        for response in responses.values():
            agreements = response.get("agreements", [])
            consensus_points.extend(agreements)

        # Find most commonly agreed points
        agreement_counts = {}
        for point in consensus_points:
            agreement_counts[point] = agreement_counts.get(point, 0) + 1

        # Return points agreed by multiple members
        return [point for point, count in agreement_counts.items() if count >= 2]

    def _extract_disagreements_from_responses(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract disagreements from peer responses."""
        disagreements = []

        for response in responses.values():
            counterpoints = response.get("counterpoints", [])
            disagreements.extend(counterpoints)

        return list(set(disagreements))  # Remove duplicates

    def _extract_member_insights(self, debate_rounds: List[DebateRound]) -> Dict[str, List[str]]:
        """Extract key insights contributed by each member across all rounds."""
        member_insights = {member.role: [] for member in self.members}

        for round_data in debate_rounds:
            # From initial reviews
            for role, review in round_data.initial_reviews.items():
                risks = review.get("overall_assessment", {}).get("top_risks", [])
                wins = review.get("overall_assessment", {}).get("quick_wins", [])
                member_insights[role].extend(risks + wins)

            # From peer responses
            for role, response in round_data.peer_responses.items():
                proposals = response.get("synthesis_proposals", [])
                questions = response.get("questions", [])
                member_insights[role].extend(proposals + questions)

        # Limit and deduplicate
        for role in member_insights:
            member_insights[role] = list(set(member_insights[role]))[:5]

        return member_insights


def should_continue_debate(debate_rounds: List[DebateRound], max_rounds: int) -> bool:
    """Determine if debate should continue based on consensus emergence."""
    if len(debate_rounds) >= max_rounds:
        return False

    if not debate_rounds:
        return True

    latest_round = debate_rounds[-1]

    # Stop if strong consensus emerged (more agreements than disagreements)
    consensus_count = len(latest_round.emerging_consensus)
    disagreement_count = len(latest_round.remaining_disagreements)

    if consensus_count >= disagreement_count * 2:  # 2:1 ratio favors consensus
        return False

    # Stop if no progress in last 2 rounds
    if len(debate_rounds) >= 2:
        prev_consensus = len(debate_rounds[-2].emerging_consensus)
        current_consensus = len(latest_round.emerging_consensus)

        if current_consensus <= prev_consensus:  # No progress
            return False

    return True


def analyze_consensus_emergence(debate_rounds: List[DebateRound]) -> ConsensusAnalysis:
    """Analyze how consensus is emerging across debate rounds."""
    if not debate_rounds:
        return ConsensusAnalysis(0.0, [], [], 0.0)

    # Track consensus growth over rounds
    consensus_counts = [len(round_data.emerging_consensus) for round_data in debate_rounds]
    disagreement_counts = [len(round_data.remaining_disagreements) for round_data in debate_rounds]

    # Calculate convergence trend
    if len(consensus_counts) >= 2:
        consensus_trend = consensus_counts[-1] - consensus_counts[0]
        disagreement_trend = disagreement_counts[0] - disagreement_counts[-1]  # Decreasing disagreements is good
        convergence_trend = (consensus_trend + disagreement_trend) / 2
    else:
        convergence_trend = 0.0

    # Get stable agreements (appear in multiple rounds)
    all_consensus = []
    for round_data in debate_rounds:
        all_consensus.extend(round_data.emerging_consensus)

    consensus_counts = {}
    for point in all_consensus:
        consensus_counts[point] = consensus_counts.get(point, 0) + 1

    stable_agreements = [point for point, count in consensus_counts.items() if count >= 2]

    # Get unresolved disagreements from latest round
    unresolved = debate_rounds[-1].remaining_disagreements if debate_rounds else []

    # Calculate confidence level
    total_consensus = len(stable_agreements)
    total_disagreements = len(unresolved)
    confidence = total_consensus / (total_consensus + total_disagreements) if (total_consensus + total_disagreements) > 0 else 0.0

    return ConsensusAnalysis(
        convergence_trend=min(1.0, max(-1.0, convergence_trend / 5)),  # Normalize to -1,1
        stable_agreements=stable_agreements,
        unresolved_disagreements=unresolved,
        confidence_level=confidence
    )


def generate_alignment_questions(disagreements: List[str]) -> List[str]:
    """Generate concrete questions to help resolve disagreements."""
    questions = []

    for disagreement in disagreements:
        disagreement_lower = disagreement.lower()

        # Pattern-based question generation
        if "cost" in disagreement_lower and "security" in disagreement_lower:
            questions.append("What's the minimum security level needed to meet cost constraints?")
        elif ("delivery" in disagreement_lower or "fast" in disagreement_lower) and ("analysis" in disagreement_lower or "thorough" in disagreement_lower):
            questions.append("What's the fastest path to deliver with adequate analysis depth?")
        elif "evaluation" in disagreement_lower and "implementation" in disagreement_lower:
            questions.append("Can we implement with basic evaluation and enhance later?")
        elif "pm" in disagreement_lower and "security" in disagreement_lower:
            # Extract the specific tension
            if "wants" in disagreement_lower:
                parts = disagreement.split("wants")
                if len(parts) >= 2:
                    pm_want = parts[1].split(",")[0].strip()
                    questions.append(f"How do we balance business needs for {pm_want} with security requirements?")
                else:
                    questions.append("How do we balance PM and Security priorities?")
            else:
                questions.append("How do we balance PM and Security priorities?")
        elif "data" in disagreement_lower and "infrastructure" in disagreement_lower:
            questions.append("How do we balance data requirements with infrastructure constraints?")
        else:
            # Generic question generation - extract key concepts
            words = disagreement.replace(",", "").split()
            key_concepts = [w for w in words if len(w) > 4 and w.lower() not in ["wants", "needs", "team"]][:3]
            if key_concepts:
                questions.append(f"How do we balance {' and '.join(key_concepts)}?")

    return questions[:5]  # Limit to 5 questions


__all__ = [
    "CouncilMember",
    "Council",
    "DebateRound",
    "DebateResult",
    "ConsensusAnalysis",
    "analyze_consensus_emergence",
    "generate_alignment_questions",
    "should_continue_debate"
]
