"""Multi-model council system with consensus and debate capabilities."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field
import statistics

from ..database.neo4j_client import Neo4jClient
from ..multi_model import MultiModelClient
from .question_engine import QuestionSet

logger = logging.getLogger(__name__)

class CouncilRole(Enum):
    """Council member roles with specific responsibilities."""
    PM = "pm"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    UX = "ux"
    DATA = "data"
    COST = "cost"

class DebateStatus(Enum):
    """Debate status tracking."""
    INITIAL = "initial"
    DEBATING = "debating"
    CONSENSUS_REACHED = "consensus_reached"
    HUMAN_ESCALATION = "human_escalation"
    RESOLVED = "resolved"

class ArgumentType(Enum):
    """Types of arguments in debates."""
    INITIAL_POSITION = "initial_position"
    COUNTER_ARGUMENT = "counter_argument"
    SUPPORTING_EVIDENCE = "supporting_evidence"
    CLARIFICATION = "clarification"
    SYNTHESIS = "synthesis"

class CouncilMember(BaseModel):
    """Individual council member with role-specific configuration."""
    role: CouncilRole
    model_provider: str  # "openai", "anthropic", "google"
    model_name: str      # "gpt-4o", "claude-3-5-sonnet", "gemini-pro"
    personality_prompt: str
    rubric_weights: Dict[str, float] = Field(default_factory=dict)
    specialty_areas: List[str] = Field(default_factory=list)
    
    @classmethod
    def create_default_members(cls) -> List[CouncilMember]:
        """Create default council members with appropriate model assignments."""
        return [
            cls(
                role=CouncilRole.PM,
                model_provider="openai",
                model_name="gpt-4o",
                personality_prompt="""You are an experienced Product Manager focused on business value, user needs, and market fit. 
                You evaluate ideas based on customer demand, market opportunity, competitive positioning, and business viability. 
                You ask tough questions about market validation, user research, and product-market fit.""",
                rubric_weights={"market_fit": 1.5, "user_value": 1.3, "business_model": 1.2},
                specialty_areas=["market_analysis", "user_research", "business_strategy", "product_roadmap"]
            ),
            cls(
                role=CouncilRole.SECURITY,
                model_provider="anthropic",
                model_name="claude-3-5-sonnet",
                personality_prompt="""You are a Security Architect who carefully analyzes risks, compliance requirements, and security implications.
                You evaluate ideas based on data protection, regulatory compliance, security vulnerabilities, and risk mitigation strategies.
                You are thorough and conservative in your assessments, always considering worst-case scenarios.""",
                rubric_weights={"security": 2.0, "compliance": 1.8, "privacy": 1.6, "risk": 1.4},
                specialty_areas=["cybersecurity", "compliance", "data_protection", "risk_assessment"]
            ),
            cls(
                role=CouncilRole.INFRASTRUCTURE,
                model_provider="google",
                model_name="gemini-pro",
                personality_prompt="""You are a Senior Infrastructure Engineer focused on scalability, reliability, and technical feasibility.
                You evaluate ideas based on system architecture, scalability requirements, performance, and operational complexity.
                You consider deployment, monitoring, maintenance, and technical debt implications.""",
                rubric_weights={"scalability": 1.6, "reliability": 1.5, "performance": 1.4, "maintainability": 1.3},
                specialty_areas=["system_architecture", "scalability", "devops", "performance_optimization"]
            ),
            cls(
                role=CouncilRole.UX,
                model_provider="openai", 
                model_name="gpt-4o",
                personality_prompt="""You are a UX Designer focused on user experience, usability, and human-centered design.
                You evaluate ideas based on user empathy, design thinking principles, accessibility, and user journey optimization.
                You advocate for the user and ensure solutions are intuitive, accessible, and delightful.""",
                rubric_weights={"usability": 1.7, "accessibility": 1.4, "user_satisfaction": 1.5, "design": 1.2},
                specialty_areas=["user_experience", "design_thinking", "accessibility", "user_research"]
            ),
            cls(
                role=CouncilRole.DATA,
                model_provider="google",
                model_name="gemini-pro", 
                personality_prompt="""You are a Data Scientist/ML Engineer focused on data strategy, analytics, and AI/ML capabilities.
                You evaluate ideas based on data requirements, analytics potential, ML/AI opportunities, and measurement strategies.
                You consider data quality, model performance, and analytical insights.""",
                rubric_weights={"data_strategy": 1.5, "analytics": 1.4, "ml_potential": 1.3, "measurement": 1.2},
                specialty_areas=["data_science", "machine_learning", "analytics", "data_engineering"]
            ),
            cls(
                role=CouncilRole.COST,
                model_provider="anthropic",
                model_name="claude-3-5-sonnet",
                personality_prompt="""You are a Financial Analyst focused on cost optimization, resource efficiency, and financial viability.
                You evaluate ideas based on development costs, operational expenses, ROI potential, and resource requirements.
                You are conservative with budget estimates and focused on sustainable economics.""",
                rubric_weights={"cost_efficiency": 1.8, "roi": 1.6, "resource_optimization": 1.4, "financial_risk": 1.3},
                specialty_areas=["financial_analysis", "cost_optimization", "budgeting", "roi_analysis"]
            )
        ]

class Argument(BaseModel):
    """Individual argument in a council debate."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    council_role: CouncilRole
    argument_type: ArgumentType
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    responds_to: Optional[str] = None  # ID of argument being responded to
    round_number: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CouncilResponse(BaseModel):
    """Individual council member response to a topic."""
    council_role: CouncilRole
    score: float = Field(ge=0.0, le=1.0)
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)
    rubric_scores: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Consensus(BaseModel):
    """Council consensus result."""
    topic_id: str
    method: str = "weighted_trimmed_mean"
    individual_scores: Dict[CouncilRole, float] = Field(default_factory=dict)
    weights: Dict[CouncilRole, float] = Field(default_factory=dict)
    raw_score: float
    weighted_score: float
    variance: float
    standard_deviation: float
    agreement_level: str  # "high", "medium", "low"
    decision: str         # "PASS", "FAIL", "ESCALATE"
    rationale: str
    consensus_threshold: float = 0.67
    variance_threshold: float = 0.3
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DebateTopic(BaseModel):
    """Topic for council debate."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    context: Dict[str, Any] = Field(default_factory=dict)
    paradigm: Optional[str] = None
    stage: str = "evaluation"  # evaluation, debate, consensus, resolved
    priority: str = "medium"   # low, medium, high, critical
    requires_human: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DebateSession(BaseModel):
    """Multi-round debate session."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    topic: DebateTopic
    participants: List[CouncilRole] = Field(default_factory=list)
    arguments: List[Argument] = Field(default_factory=list)
    current_round: int = 1
    max_rounds: int = 3
    status: DebateStatus = DebateStatus.INITIAL
    consensus: Optional[Consensus] = None
    human_decision: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class CouncilSystem:
    """Multi-model council system with debate and consensus capabilities."""
    
    def __init__(
        self,
        neo4j_client: Neo4jClient,
        multi_model_client: MultiModelClient,
        council_members: Optional[List[CouncilMember]] = None
    ):
        self.neo4j = neo4j_client
        self.multi_model = multi_model_client
        self.members = council_members or CouncilMember.create_default_members()
        self.active_debates: Dict[str, DebateSession] = {}
    
    async def evaluate_topic(
        self,
        topic: DebateTopic,
        enable_debate: bool = True,
        consensus_threshold: float = 0.67,
        variance_threshold: float = 0.3
    ) -> Tuple[Consensus, Optional[DebateSession]]:
        """Evaluate a topic with optional multi-round debate."""
        
        # Step 1: Get initial positions from all council members
        initial_responses = await self._get_initial_responses(topic)
        
        # Step 2: Calculate initial consensus
        consensus = self._calculate_consensus(
            topic.id, 
            initial_responses,
            consensus_threshold,
            variance_threshold
        )
        
        # Step 3: If consensus not reached and debate enabled, start debate
        debate_session = None
        if (consensus.decision == "ESCALATE" and enable_debate and 
            not topic.requires_human and consensus.variance > variance_threshold):
            
            debate_session = await self._conduct_debate(topic, initial_responses)
            
            # Recalculate consensus after debate
            if debate_session.status == DebateStatus.CONSENSUS_REACHED:
                final_responses = self._extract_final_positions(debate_session)
                consensus = self._calculate_consensus(
                    topic.id,
                    final_responses, 
                    consensus_threshold,
                    variance_threshold
                )
        
        # Step 4: Store results in Neo4j
        await self._store_evaluation_results(topic, consensus, debate_session)
        
        return consensus, debate_session
    
    async def _get_initial_responses(
        self, 
        topic: DebateTopic
    ) -> List[CouncilResponse]:
        """Get initial responses from all council members."""
        
        tasks = []
        for member in self.members:
            task = self._get_member_response(member, topic)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Failed to get response from {self.members[i].role}: {response}")
            else:
                valid_responses.append(response)
        
        return valid_responses
    
    async def _get_member_response(
        self,
        member: CouncilMember,
        topic: DebateTopic
    ) -> CouncilResponse:
        """Get response from a single council member."""
        
        prompt = f"""
        {member.personality_prompt}
        
        Please evaluate the following topic from your role perspective:
        
        Title: {topic.title}
        Description: {topic.description}
        
        Context:
        {self._format_context(topic.context)}
        
        Provide your evaluation as a score from 0.0 to 1.0, where:
        - 0.0-0.3: Strong concerns, not recommended
        - 0.4-0.6: Mixed assessment, needs significant improvements  
        - 0.7-0.8: Good with minor concerns
        - 0.9-1.0: Excellent, strongly recommended
        
        Also provide specific rubric scores for your specialty areas: {member.specialty_areas}
        
        Respond in JSON format:
        {{
            "score": 0.75,
            "confidence": 0.85,
            "rationale": "detailed explanation of your assessment",
            "rubric_scores": {{"area1": 0.8, "area2": 0.7}},
            "recommendations": ["specific recommendation 1", "recommendation 2"],
            "concerns": ["concern 1", "concern 2"]
        }}
        """
        
        response = await self.multi_model.call_model(
            model=f"{member.model_provider}/{member.model_name}",
            messages=[{"role": "user", "content": prompt}],
            response_format="json"
        )
        
        return CouncilResponse(
            council_role=member.role,
            **response
        )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into readable text."""
        
        formatted = []
        for key, value in context.items():
            if isinstance(value, list):
                formatted.append(f"- {key}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                formatted.append(f"- {key}: {value}")
            else:
                formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _calculate_consensus(
        self,
        topic_id: str,
        responses: List[CouncilResponse],
        consensus_threshold: float = 0.67,
        variance_threshold: float = 0.3
    ) -> Consensus:
        """Calculate weighted consensus from council responses."""
        
        if not responses:
            return Consensus(
                topic_id=topic_id,
                raw_score=0.0,
                weighted_score=0.0,
                variance=1.0,
                standard_deviation=1.0,
                agreement_level="none",
                decision="FAIL",
                rationale="No responses received"
            )
        
        # Extract scores and calculate basic statistics
        scores = [r.score for r in responses]
        raw_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        variance = std_dev ** 2
        
        # Calculate weighted score
        total_weight = 0.0
        weighted_sum = 0.0
        weights = {}
        
        for response in responses:
            # Base weight of 1.0, adjusted by confidence
            weight = 1.0 * response.confidence
            weights[response.council_role] = weight
            weighted_sum += response.score * weight
            total_weight += weight
        
        weighted_score = weighted_sum / total_weight if total_weight > 0 else raw_score
        
        # Determine agreement level
        if std_dev <= 0.1:
            agreement_level = "high"
        elif std_dev <= variance_threshold:
            agreement_level = "medium" 
        else:
            agreement_level = "low"
        
        # Make decision
        if variance > variance_threshold:
            decision = "ESCALATE"
            rationale = f"High variance ({variance:.3f}) requires human review or debate"
        elif weighted_score >= consensus_threshold:
            decision = "PASS"
            rationale = f"Consensus reached with score {weighted_score:.3f} above threshold {consensus_threshold}"
        else:
            decision = "FAIL"
            rationale = f"Consensus score {weighted_score:.3f} below threshold {consensus_threshold}"
        
        # Extract individual scores for record
        individual_scores = {r.council_role: r.score for r in responses}
        
        return Consensus(
            topic_id=topic_id,
            individual_scores=individual_scores,
            weights=weights,
            raw_score=raw_score,
            weighted_score=weighted_score,
            variance=variance,
            standard_deviation=std_dev,
            agreement_level=agreement_level,
            decision=decision,
            rationale=rationale,
            consensus_threshold=consensus_threshold,
            variance_threshold=variance_threshold
        )
    
    async def _conduct_debate(
        self,
        topic: DebateTopic,
        initial_responses: List[CouncilResponse]
    ) -> DebateSession:
        """Conduct multi-round debate between council members."""
        
        debate_session = DebateSession(
            topic=topic,
            participants=[r.council_role for r in initial_responses],
            max_rounds=3,
            status=DebateStatus.INITIAL
        )
        
        # Convert initial responses to initial position arguments
        for response in initial_responses:
            argument = Argument(
                council_role=response.council_role,
                argument_type=ArgumentType.INITIAL_POSITION,
                content=response.rationale,
                confidence=response.confidence,
                round_number=1
            )
            debate_session.arguments.append(argument)
        
        debate_session.status = DebateStatus.DEBATING
        self.active_debates[debate_session.id] = debate_session
        
        # Conduct debate rounds
        for round_num in range(2, debate_session.max_rounds + 1):
            debate_session.current_round = round_num
            
            # Generate counter-arguments for this round
            new_arguments = await self._generate_counter_arguments(debate_session, round_num)
            debate_session.arguments.extend(new_arguments)
            
            # Check if consensus emerges
            if await self._check_debate_convergence(debate_session):
                debate_session.status = DebateStatus.CONSENSUS_REACHED
                break
        
        # If no convergence after max rounds, escalate to human
        if debate_session.status == DebateStatus.DEBATING:
            debate_session.status = DebateStatus.HUMAN_ESCALATION
        
        debate_session.updated_at = datetime.utcnow()
        return debate_session
    
    async def _generate_counter_arguments(
        self, 
        debate_session: DebateSession,
        round_number: int
    ) -> List[Argument]:
        """Generate counter-arguments for current debate round."""
        
        counter_arguments = []
        
        # Get previous round arguments
        previous_args = [
            arg for arg in debate_session.arguments 
            if arg.round_number == round_number - 1
        ]
        
        for member in self.members:
            if member.role not in debate_session.participants:
                continue
            
            # Get member's previous arguments
            member_previous = [
                arg for arg in previous_args
                if arg.council_role == member.role
            ]
            
            # Get other members' arguments to respond to
            others_args = [
                arg for arg in previous_args
                if arg.council_role != member.role
            ]
            
            if not others_args:
                continue
            
            # Generate counter-argument
            counter_arg = await self._generate_member_counter_argument(
                member, member_previous, others_args, debate_session.topic, round_number
            )
            
            if counter_arg:
                counter_arguments.append(counter_arg)
        
        return counter_arguments
    
    async def _generate_member_counter_argument(
        self,
        member: CouncilMember,
        member_previous_args: List[Argument],
        peer_arguments: List[Argument],
        topic: DebateTopic,
        round_number: int
    ) -> Optional[Argument]:
        """Generate counter-argument from a specific member."""
        
        # Format peer arguments
        peer_content = []
        for arg in peer_arguments:
            peer_content.append(f"{arg.council_role.value}: {arg.content}")
        
        prompt = f"""
        {member.personality_prompt}
        
        You are participating in a council debate about: {topic.title}
        
        Your previous position:
        {member_previous_args[0].content if member_previous_args else "No previous position"}
        
        Other council members' arguments:
        {chr(10).join(peer_content)}
        
        Based on the peer arguments, provide a thoughtful response that either:
        1. Addresses concerns raised by peers
        2. Provides additional evidence for your position  
        3. Finds common ground or synthesis
        4. Identifies new considerations
        
        Keep your response focused and constructive. Avoid repeating your previous arguments.
        
        Respond in JSON format:
        {{
            "content": "your counter-argument or synthesis",
            "confidence": 0.85,
            "argument_type": "counter_argument",
            "responds_to": "role_name or null"
        }}
        """
        
        try:
            response = await self.multi_model.call_model(
                model=f"{member.model_provider}/{member.model_name}",
                messages=[{"role": "user", "content": prompt}],
                response_format="json"
            )
            
            return Argument(
                council_role=member.role,
                argument_type=ArgumentType(response.get("argument_type", "counter_argument")),
                content=response["content"],
                confidence=response.get("confidence", 0.5),
                responds_to=response.get("responds_to"),
                round_number=round_number
            )
        
        except Exception as e:
            logger.error(f"Failed to generate counter-argument for {member.role}: {e}")
            return None
    
    async def _check_debate_convergence(self, debate_session: DebateSession) -> bool:
        """Check if debate has converged to consensus."""
        
        # Get latest arguments from each participant
        latest_positions = {}
        for participant in debate_session.participants:
            participant_args = [
                arg for arg in debate_session.arguments
                if arg.council_role == participant
            ]
            if participant_args:
                latest_positions[participant] = participant_args[-1]
        
        # Look for convergence indicators in the language
        convergence_indicators = [
            "i agree", "good point", "consensus", "common ground", 
            "synthesis", "balanced approach", "compromise"
        ]
        
        convergence_count = 0
        for arg in latest_positions.values():
            if any(indicator in arg.content.lower() for indicator in convergence_indicators):
                convergence_count += 1
        
        # Consider convergence if majority show agreement
        return convergence_count >= len(latest_positions) * 0.6
    
    def _extract_final_positions(self, debate_session: DebateSession) -> List[CouncilResponse]:
        """Extract final positions from debate session as council responses."""
        
        final_responses = []
        
        for participant in debate_session.participants:
            participant_args = [
                arg for arg in debate_session.arguments
                if arg.council_role == participant
            ]
            
            if participant_args:
                latest_arg = participant_args[-1]
                
                # Extract score from confidence (this is simplified)
                # In practice, you'd want to ask LLM for updated score
                score = latest_arg.confidence * 0.8 + 0.2  # Adjust confidence to score range
                
                response = CouncilResponse(
                    council_role=participant,
                    score=score,
                    rationale=latest_arg.content,
                    confidence=latest_arg.confidence
                )
                final_responses.append(response)
        
        return final_responses
    
    async def _store_evaluation_results(
        self,
        topic: DebateTopic,
        consensus: Consensus,
        debate_session: Optional[DebateSession]
    ) -> None:
        """Store evaluation results in Neo4j."""
        
        query = """
        MERGE (t:Topic {id: $topic_id})
        SET t.title = $title,
            t.description = $description,
            t.stage = $stage,
            t.priority = $priority,
            t.created_at = datetime()
        
        MERGE (c:Consensus {id: $consensus_id})
        SET c.topic_id = $topic_id,
            c.method = $method,
            c.raw_score = $raw_score,
            c.weighted_score = $weighted_score,
            c.variance = $variance,
            c.standard_deviation = $standard_deviation,
            c.agreement_level = $agreement_level,
            c.decision = $decision,
            c.rationale = $rationale,
            c.created_at = datetime()
        
        MERGE (t)-[:HAS_CONSENSUS]->(c)
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            session.run(query, {
                "topic_id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "stage": topic.stage,
                "priority": topic.priority,
                "consensus_id": str(uuid4()),
                "method": consensus.method,
                "raw_score": consensus.raw_score,
                "weighted_score": consensus.weighted_score,
                "variance": consensus.variance,
                "standard_deviation": consensus.standard_deviation,
                "agreement_level": consensus.agreement_level,
                "decision": consensus.decision,
                "rationale": consensus.rationale
            })
        
        # Store debate session if it exists
        if debate_session:
            await self._store_debate_session(debate_session)
    
    async def _store_debate_session(self, debate_session: DebateSession) -> None:
        """Store debate session and arguments in Neo4j."""
        
        # Store debate session
        query = """
        MERGE (d:DebateSession {id: $debate_id})
        SET d.topic_id = $topic_id,
            d.current_round = $current_round,
            d.max_rounds = $max_rounds,
            d.status = $status,
            d.created_at = datetime(),
            d.updated_at = datetime()
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            session.run(query, {
                "debate_id": debate_session.id,
                "topic_id": debate_session.topic.id,
                "current_round": debate_session.current_round,
                "max_rounds": debate_session.max_rounds,
                "status": debate_session.status.value
            })
            
            # Store arguments
            for arg in debate_session.arguments:
                arg_query = """
                MERGE (a:Argument {id: $arg_id})
                SET a.debate_session_id = $debate_id,
                    a.council_role = $role,
                    a.argument_type = $arg_type,
                    a.content = $content,
                    a.confidence = $confidence,
                    a.round_number = $round_number,
                    a.responds_to = $responds_to,
                    a.created_at = datetime()
                """
                
                session.run(arg_query, {
                    "arg_id": arg.id,
                    "debate_id": debate_session.id,
                    "role": arg.council_role.value,
                    "arg_type": arg.argument_type.value,
                    "content": arg.content,
                    "confidence": arg.confidence,
                    "round_number": arg.round_number,
                    "responds_to": arg.responds_to
                })
    
    def escalate_to_human(
        self,
        topic_id: str,
        reason: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Escalate decision to human review."""
        
        escalation = {
            "topic_id": topic_id,
            "reason": reason,
            "context": context,
            "requires_human_decision": True,
            "escalated_at": datetime.utcnow().isoformat(),
            "status": "pending_human_review"
        }
        
        # Store escalation in Neo4j
        query = """
        MATCH (t:Topic {id: $topic_id})
        MERGE (e:HumanEscalation {id: $escalation_id})
        SET e.topic_id = $topic_id,
            e.reason = $reason,
            e.context = $context,
            e.status = 'pending',
            e.created_at = datetime()
        MERGE (t)-[:REQUIRES_HUMAN_REVIEW]->(e)
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            session.run(query, {
                "topic_id": topic_id,
                "escalation_id": str(uuid4()),
                "reason": reason,
                "context": str(context)
            })
        
        return escalation
    
    def get_debate_transcript(self, debate_id: str) -> Optional[DebateSession]:
        """Get debate session with full transcript."""
        return self.active_debates.get(debate_id)
    
    def get_council_statistics(self) -> Dict[str, Any]:
        """Get council performance statistics."""
        
        query = """
        MATCH (c:Consensus)
        WITH count(c) as total,
             sum(CASE WHEN c.decision = 'PASS' THEN 1 ELSE 0 END) as passed,
             sum(CASE WHEN c.decision = 'FAIL' THEN 1 ELSE 0 END) as failed,
             sum(CASE WHEN c.decision = 'ESCALATE' THEN 1 ELSE 0 END) as escalated,
             avg(c.weighted_score) as avg_score,
             avg(c.variance) as avg_variance
        RETURN {
            total_evaluations: total,
            pass_rate: CASE WHEN total > 0 THEN toFloat(passed) / total ELSE 0.0 END,
            escalation_rate: CASE WHEN total > 0 THEN toFloat(escalated) / total ELSE 0.0 END,
            average_score: avg_score,
            average_variance: avg_variance
        } as stats
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(query)
            record = result.single()
            return record["stats"] if record else {}
