"""Council service for managing debate and consensus building.

Handles council member coordination, debate orchestration, and consensus
tracking with proper separation of concerns and event-driven architecture.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum

from ..interfaces import IEventPublisher, IMetricsCollector, ICacheService


logger = logging.getLogger(__name__)


class DebateStatus(Enum):
    """Status of a council debate."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CouncilMemberInfo:
    """Information about a council member."""
    member_id: str
    role: str
    provider: str
    model: str
    expertise_areas: List[str]
    personality: str
    debate_style: str
    current_status: str = "idle"
    insights_contributed: int = 0
    agreements_made: int = 0
    questions_asked: int = 0


@dataclass
class DebateRound:
    """Represents a single round of debate."""
    round_number: int
    participants: List[str]
    initial_reviews: Dict[str, Dict[str, Any]]
    peer_responses: Dict[str, Dict[str, Any]]
    emerging_consensus: List[str]
    disagreements: List[str]
    questions_raised: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    status: DebateStatus = DebateStatus.PENDING


@dataclass
class DebateSession:
    """Complete debate session information."""
    session_id: str
    document_stage: str
    participants: List[CouncilMemberInfo]
    rounds: List[DebateRound]
    final_consensus: List[str]
    unresolved_issues: List[str]
    consensus_score: float
    total_duration: float
    status: DebateStatus
    created_at: float
    completed_at: Optional[float] = None


class CouncilService:
    """Service for managing council debates and consensus building."""

    def __init__(
        self,
        event_publisher: IEventPublisher,
        metrics_collector: IMetricsCollector,
        cache_service: ICacheService,
        max_debate_rounds: int = 3,
        consensus_threshold: float = 0.7
    ):
        self._event_publisher = event_publisher
        self._metrics_collector = metrics_collector
        self._cache_service = cache_service
        self._max_debate_rounds = max_debate_rounds
        self._consensus_threshold = consensus_threshold

        self._active_sessions: Dict[str, DebateSession] = {}
        self._council_members: Dict[str, CouncilMemberInfo] = {}

        logger.info(f"CouncilService initialized (max_rounds={max_debate_rounds})")

    def register_council_member(
        self,
        member_id: str,
        role: str,
        provider: str,
        model: str,
        expertise_areas: List[str],
        personality: str = "balanced",
        debate_style: str = "collaborative"
    ) -> CouncilMemberInfo:
        """Register a new council member."""
        member_info = CouncilMemberInfo(
            member_id=member_id,
            role=role,
            provider=provider,
            model=model,
            expertise_areas=expertise_areas,
            personality=personality,
            debate_style=debate_style
        )

        self._council_members[member_id] = member_info

        logger.info(f"Registered council member: {role} ({provider}/{model})")
        return member_info

    def get_council_members(self) -> List[CouncilMemberInfo]:
        """Get all registered council members."""
        return list(self._council_members.values())

    def get_member_by_role(self, role: str) -> Optional[CouncilMemberInfo]:
        """Get council member by role."""
        return next(
            (member for member in self._council_members.values() if member.role == role),
            None
        )

    async def start_debate_session(
        self,
        document_content: str,
        document_stage: str,
        participant_roles: Optional[List[str]] = None
    ) -> str:
        """Start a new debate session."""
        session_id = self._generate_session_id(document_stage)

        # Select participants
        if participant_roles:
            participants = [
                member for member in self._council_members.values()
                if member.role in participant_roles
            ]
        else:
            participants = list(self._council_members.values())

        if not participants:
            raise ValueError("No council members available for debate")

        # Create session
        session = DebateSession(
            session_id=session_id,
            document_stage=document_stage,
            participants=participants,
            rounds=[],
            final_consensus=[],
            unresolved_issues=[],
            consensus_score=0.0,
            total_duration=0.0,
            status=DebateStatus.PENDING,
            created_at=time.time()
        )

        self._active_sessions[session_id] = session

        # Publish session started event
        await self._event_publisher.publish("debate_session_started", {
            "session_id": session_id,
            "stage": document_stage,
            "participants": [p.role for p in participants],
            "max_rounds": self._max_debate_rounds
        })

        logger.info(f"Started debate session {session_id} for {document_stage}")
        return session_id

    async def conduct_debate(
        self,
        session_id: str,
        document_content: str
    ) -> DebateSession:
        """Conduct the full debate session."""
        if session_id not in self._active_sessions:
            raise ValueError(f"Debate session not found: {session_id}")

        session = self._active_sessions[session_id]
        session.status = DebateStatus.IN_PROGRESS
        start_time = time.time()

        try:
            # Update member status
            await self._update_member_status(session.participants, "debating")

            # Conduct debate rounds
            for round_num in range(1, self._max_debate_rounds + 1):
                round_result = await self._execute_debate_round(
                    session,
                    round_num,
                    document_content
                )

                session.rounds.append(round_result)

                # Check if consensus reached
                if await self._check_consensus_reached(session):
                    logger.info(f"Consensus reached in round {round_num}")
                    break

                # Publish round completed event
                await self._event_publisher.publish("debate_round_completed", {
                    "session_id": session_id,
                    "round_number": round_num,
                    "consensus_points": len(round_result.emerging_consensus),
                    "disagreements": len(round_result.disagreements)
                })

            # Finalize session
            session.final_consensus = await self._extract_final_consensus(session)
            session.unresolved_issues = await self._extract_unresolved_issues(session)
            session.consensus_score = await self._calculate_consensus_score(session)
            session.total_duration = time.time() - start_time
            session.completed_at = time.time()
            session.status = DebateStatus.COMPLETED

            # Update member status
            await self._update_member_status(session.participants, "idle")

            # Record metrics
            self._metrics_collector.record_audit_duration(
                session.total_duration,
                session.document_stage,
                "council_debate"
            )

            # Publish session completed event
            await self._event_publisher.publish("debate_session_completed", {
                "session_id": session_id,
                "success": session.consensus_score >= self._consensus_threshold,
                "rounds": len(session.rounds),
                "consensus_score": session.consensus_score,
                "duration": session.total_duration
            })

            logger.info(f"Debate session {session_id} completed in {session.total_duration:.2f}s")
            return session

        except Exception as e:
            session.status = DebateStatus.FAILED
            session.completed_at = time.time()

            await self._update_member_status(session.participants, "idle")

            await self._event_publisher.publish("debate_session_failed", {
                "session_id": session_id,
                "error": str(e)
            })

            logger.error(f"Debate session {session_id} failed: {e}")
            raise

    async def _execute_debate_round(
        self,
        session: DebateSession,
        round_number: int,
        document_content: str
    ) -> DebateRound:
        """Execute a single debate round."""
        start_time = time.time()

        round_data = DebateRound(
            round_number=round_number,
            participants=[p.member_id for p in session.participants],
            initial_reviews={},
            peer_responses={},
            emerging_consensus=[],
            disagreements=[],
            status=DebateStatus.IN_PROGRESS
        )

        if round_number == 1:
            # Initial reviews round
            round_data.initial_reviews = await self._collect_initial_reviews(
                session.participants,
                document_content,
                session.document_stage
            )

            round_data.emerging_consensus = self._extract_consensus_themes(
                round_data.initial_reviews
            )
            round_data.disagreements = self._extract_disagreement_themes(
                round_data.initial_reviews
            )

        else:
            # Peer response round
            previous_reviews = self._collect_previous_reviews(session.rounds)
            round_data.peer_responses = await self._collect_peer_responses(
                session.participants,
                previous_reviews,
                document_content,
                session.document_stage
            )

            round_data.emerging_consensus = self._extract_consensus_from_responses(
                round_data.peer_responses
            )
            round_data.disagreements = self._extract_disagreements_from_responses(
                round_data.peer_responses
            )
            round_data.questions_raised = self._extract_questions_from_responses(
                round_data.peer_responses
            )

        round_data.duration_seconds = time.time() - start_time
        round_data.status = DebateStatus.COMPLETED

        return round_data

    async def _collect_initial_reviews(
        self,
        participants: List[CouncilMemberInfo],
        document_content: str,
        stage: str
    ) -> Dict[str, Dict[str, Any]]:
        """Collect initial reviews from all participants."""
        # This would integrate with the actual council member implementations
        # For now, return mock data structure
        reviews = {}

        for participant in participants:
            # Update member status
            participant.current_status = "reviewing"

            # Mock review (in real implementation, call participant.provide_review)
            reviews[participant.role] = {
                "auditor_role": participant.role,
                "overall_assessment": {
                    "summary": f"Review from {participant.role}",
                    "top_risks": [f"{participant.role} identified risk 1", f"{participant.role} identified risk 2"],
                    "quick_wins": [f"{participant.role} suggested improvement 1"]
                }
            }

            participant.insights_contributed += 2  # Mock increment

        return reviews

    async def _collect_peer_responses(
        self,
        participants: List[CouncilMemberInfo],
        previous_reviews: List[Dict[str, Any]],
        document_content: str,
        stage: str
    ) -> Dict[str, Dict[str, Any]]:
        """Collect responses to peer feedback."""
        responses = {}

        for participant in participants:
            participant.current_status = "responding"

            # Mock response (in real implementation, call participant.respond_to_peers)
            responses[participant.role] = {
                "questions": [f"Question from {participant.role}"],
                "agreements": [f"Agreement from {participant.role}"],
                "counterpoints": [f"Counterpoint from {participant.role}"],
                "synthesis_proposals": [f"Proposal from {participant.role}"]
            }

            participant.questions_asked += 1
            participant.agreements_made += 1

        return responses

    def _collect_previous_reviews(self, rounds: List[DebateRound]) -> List[Dict[str, Any]]:
        """Collect all previous reviews from completed rounds."""
        all_reviews = []
        for round_data in rounds:
            all_reviews.extend(round_data.initial_reviews.values())
        return all_reviews

    def _extract_consensus_themes(self, reviews: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract consensus themes from initial reviews."""
        # Simple implementation - look for common keywords
        themes = []
        all_content = []

        for review in reviews.values():
            summary = review.get("overall_assessment", {}).get("summary", "")
            all_content.append(summary.lower())

        # Find common themes
        common_words = ["security", "performance", "quality", "user", "cost"]
        for word in common_words:
            if sum(1 for content in all_content if word in content) >= 2:
                themes.append(f"Multiple reviewers emphasize {word}")

        return themes[:5]

    def _extract_disagreement_themes(self, reviews: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract disagreement themes from reviews."""
        disagreements = []

        # Compare risk priorities
        all_risks = []
        for review in reviews.values():
            risks = review.get("overall_assessment", {}).get("top_risks", [])
            all_risks.extend(risks)

        if len(set(all_risks)) > len(all_risks) * 0.7:
            disagreements.append("Significant disagreement on risk prioritization")

        return disagreements

    def _extract_consensus_from_responses(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract consensus points from peer responses."""
        consensus_points = []
        for response in responses.values():
            agreements = response.get("agreements", [])
            consensus_points.extend(agreements)
        return list(set(consensus_points))  # Remove duplicates

    def _extract_disagreements_from_responses(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract disagreements from peer responses."""
        disagreements = []
        for response in responses.values():
            counterpoints = response.get("counterpoints", [])
            disagreements.extend(counterpoints)
        return list(set(disagreements))

    def _extract_questions_from_responses(self, responses: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract questions raised from peer responses."""
        questions = []
        for response in responses.values():
            response_questions = response.get("questions", [])
            questions.extend(response_questions)
        return list(set(questions))

    async def _check_consensus_reached(self, session: DebateSession) -> bool:
        """Check if sufficient consensus has been reached."""
        if not session.rounds:
            return False

        latest_round = session.rounds[-1]
        consensus_count = len(latest_round.emerging_consensus)
        disagreement_count = len(latest_round.disagreements)

        # Simple heuristic: consensus reached if more consensus than disagreements
        return consensus_count > disagreement_count and consensus_count >= 3

    async def _extract_final_consensus(self, session: DebateSession) -> List[str]:
        """Extract final consensus from all rounds."""
        all_consensus = []
        for round_data in session.rounds:
            all_consensus.extend(round_data.emerging_consensus)

        # Count occurrences and return most frequent
        consensus_counts = {}
        for point in all_consensus:
            consensus_counts[point] = consensus_counts.get(point, 0) + 1

        # Return points that appeared in multiple rounds
        return [point for point, count in consensus_counts.items() if count >= 2]

    async def _extract_unresolved_issues(self, session: DebateSession) -> List[str]:
        """Extract unresolved issues from the session."""
        if session.rounds:
            return session.rounds[-1].disagreements
        return []

    async def _calculate_consensus_score(self, session: DebateSession) -> float:
        """Calculate overall consensus score for the session."""
        if not session.rounds:
            return 0.0

        consensus_count = len(session.final_consensus)
        disagreement_count = len(session.unresolved_issues)

        if consensus_count + disagreement_count == 0:
            return 0.0

        return consensus_count / (consensus_count + disagreement_count)

    async def _update_member_status(
        self,
        participants: List[CouncilMemberInfo],
        status: str
    ) -> None:
        """Update status for all participants."""
        for participant in participants:
            participant.current_status = status

    def _generate_session_id(self, stage: str) -> str:
        """Generate unique session ID."""
        import hashlib
        import time
        content = f"{stage}:{time.time()}"
        return f"debate_{hashlib.md5(content.encode()).hexdigest()[:8]}"

    def get_active_sessions(self) -> List[DebateSession]:
        """Get all active debate sessions."""
        return [
            session for session in self._active_sessions.values()
            if session.status in [DebateStatus.PENDING, DebateStatus.IN_PROGRESS]
        ]

    def get_session(self, session_id: str) -> Optional[DebateSession]:
        """Get debate session by ID."""
        return self._active_sessions.get(session_id)

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel an active debate session."""
        if session_id not in self._active_sessions:
            return False

        session = self._active_sessions[session_id]
        if session.status in [DebateStatus.PENDING, DebateStatus.IN_PROGRESS]:
            session.status = DebateStatus.CANCELLED
            session.completed_at = time.time()

            await self._update_member_status(session.participants, "idle")

            await self._event_publisher.publish("debate_session_cancelled", {
                "session_id": session_id
            })

            logger.info(f"Cancelled debate session {session_id}")
            return True

        return False


__all__ = [
    "CouncilService",
    "CouncilMemberInfo",
    "DebateSession",
    "DebateRound",
    "DebateStatus"
]
