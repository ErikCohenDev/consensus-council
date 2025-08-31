"""Question generation engine with paradigm support and human-in-loop integration."""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from pydantic import BaseModel, Field
import yaml

from ..database.neo4j_client import Neo4jClient
from ..models.idea_models import IdeaGraph, ExtractedEntities
from ..multi_model import MultiModelClient
from .research_expander import ResearchContext

logger = logging.getLogger(__name__)

class QuestionPriority(Enum):
    """Question priority levels."""
    CRITICAL = "critical"
    IMPORTANT = "important"
    NICE_TO_HAVE = "nice_to_have"

class QuestionType(Enum):
    """Question types for categorization."""
    HUMAN_REQUIRED = "human_required"
    LLM_ANSWERABLE = "llm_answerable"
    RESEARCH_ANSWERABLE = "research_answerable"

class Paradigm(Enum):
    """Supported development paradigms."""
    YC = "yc"
    MCKINSEY = "mckinsey" 
    LEAN = "lean_startup"
    DESIGN_THINKING = "design_thinking"

class Question(BaseModel):
    """Individual question with context and metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    text: str
    paradigm: Paradigm
    category: str  # e.g., "problem_validation", "market_size", "icp_definition"
    priority: QuestionPriority
    question_type: QuestionType
    context: Dict[str, Any] = Field(default_factory=dict)
    related_entities: List[str] = Field(default_factory=list)
    suggested_answer: Optional[str] = None
    confidence: float = 0.0
    human_answer: Optional[str] = None
    answer_rationale: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    answered_at: Optional[datetime] = None

class QuestionSet(BaseModel):
    """Collection of questions for a paradigm with metadata."""
    paradigm: Paradigm
    idea_id: str
    questions: List[Question]
    completion_rate: float = 0.0
    critical_questions_answered: int = 0
    total_critical_questions: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ReviewSession(BaseModel):
    """Human review session for question answering."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    question_set_id: str
    current_question_index: int = 0
    completed_questions: List[str] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)
    session_data: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"  # active, paused, completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class QuestionEngine:
    """Question generation engine with paradigm support."""
    
    def __init__(
        self, 
        neo4j_client: Neo4jClient,
        multi_model_client: MultiModelClient,
        templates_dir: str = "config/paradigm_templates"
    ):
        self.neo4j = neo4j_client
        self.multi_model = multi_model_client
        self.templates_dir = templates_dir
        self.paradigm_templates = {}
        self._load_paradigm_templates()
    
    def _load_paradigm_templates(self) -> None:
        """Load paradigm-specific question templates."""
        paradigm_files = {
            Paradigm.YC: "yc_framework.yaml",
            Paradigm.MCKINSEY: "mckinsey_framework.yaml",
            Paradigm.LEAN: "lean_startup_framework.yaml",
            Paradigm.DESIGN_THINKING: "design_thinking_framework.yaml"
        }
        
        for paradigm, filename in paradigm_files.items():
            try:
                with open(f"{self.templates_dir}/{filename}", 'r') as f:
                    self.paradigm_templates[paradigm] = yaml.safe_load(f)
                logger.info(f"Loaded template for {paradigm.value}")
            except FileNotFoundError:
                logger.warning(f"Template file not found: {filename}")
                # Provide fallback templates
                self.paradigm_templates[paradigm] = self._get_fallback_template(paradigm)
    
    def _get_fallback_template(self, paradigm: Paradigm) -> Dict[str, Any]:
        """Get fallback template when file is not available."""
        templates = {
            Paradigm.YC: {
                "name": "Y Combinator Framework",
                "description": "Market-first approach focusing on user problems and solutions",
                "required_fields": ["problem", "target_users", "solution", "market_size", "competition", "business_model"],
                "question_categories": {
                    "problem_validation": {
                        "questions": [
                            "What specific problem does your product solve?",
                            "How acute is this problem for your target users?",
                            "What do people currently do to solve this problem?",
                            "How do you know this is a real problem people will pay to solve?"
                        ],
                        "priority": "critical"
                    },
                    "market_validation": {
                        "questions": [
                            "Who are your target users specifically?",
                            "How big is your target market?",
                            "Who are your main competitors?",
                            "What's your unfair advantage?"
                        ],
                        "priority": "critical"
                    },
                    "solution_validation": {
                        "questions": [
                            "What's the simplest version of your solution?",
                            "How will you acquire your first customers?",
                            "What's your revenue model?",
                            "What are the key metrics you'll track?"
                        ],
                        "priority": "important"
                    }
                }
            },
            Paradigm.MCKINSEY: {
                "name": "McKinsey Problem-Solving Framework",
                "description": "MECE approach with hypothesis-driven analysis",
                "required_fields": ["problem_statement", "hypothesis", "analysis_plan", "data_sources", "decision_criteria"],
                "question_categories": {
                    "problem_definition": {
                        "questions": [
                            "What is the core problem statement?",
                            "What are the key symptoms vs root causes?",
                            "How can we break this down using MECE principles?",
                            "What's the business impact of not solving this?"
                        ],
                        "priority": "critical"
                    },
                    "hypothesis_formation": {
                        "questions": [
                            "What's your initial hypothesis about the solution?",
                            "What assumptions underlie your hypothesis?",
                            "What would need to be true for this to succeed?",
                            "What are the alternative hypotheses?"
                        ],
                        "priority": "critical"
                    },
                    "analysis_planning": {
                        "questions": [
                            "What data do you need to test your hypothesis?",
                            "What analysis methods will you use?",
                            "What are your decision criteria?",
                            "How will you measure success?"
                        ],
                        "priority": "important"
                    }
                }
            },
            Paradigm.LEAN: {
                "name": "Lean Startup Framework", 
                "description": "Build-Measure-Learn cycle with validated learning",
                "required_fields": ["value_hypothesis", "growth_hypothesis", "mvp_definition", "metrics", "pivot_criteria"],
                "question_categories": {
                    "hypothesis_definition": {
                        "questions": [
                            "What's your value hypothesis?",
                            "What's your growth hypothesis?", 
                            "What assumptions are riskiest?",
                            "How will you validate these assumptions?"
                        ],
                        "priority": "critical"
                    },
                    "mvp_design": {
                        "questions": [
                            "What's the minimum viable product?",
                            "What features are essential vs nice-to-have?",
                            "How will you measure learning?",
                            "What's your build-measure-learn cycle?"
                        ],
                        "priority": "critical"
                    },
                    "metrics_and_learning": {
                        "questions": [
                            "What are your key metrics?",
                            "How will you know if you should pivot?",
                            "What would make you persevere?",
                            "How will you accelerate learning?"
                        ],
                        "priority": "important"
                    }
                }
            },
            Paradigm.DESIGN_THINKING: {
                "name": "Design Thinking Framework",
                "description": "Human-centered design process",
                "required_fields": ["user_needs", "pain_points", "empathy_insights", "ideation_results", "prototype_plan"],
                "question_categories": {
                    "empathy_understanding": {
                        "questions": [
                            "Who are you designing for specifically?",
                            "What are their main pain points?",
                            "What do they currently do to solve this?",
                            "What emotional needs does this address?"
                        ],
                        "priority": "critical"
                    },
                    "problem_definition": {
                        "questions": [
                            "How might we frame the core problem?",
                            "What's the user's journey currently?",
                            "What opportunities do you see?",
                            "What constraints do you need to work within?"
                        ],
                        "priority": "critical"
                    },
                    "ideation_and_prototyping": {
                        "questions": [
                            "What solution ideas have you generated?",
                            "Which ideas show the most promise?",
                            "How will you prototype and test?",
                            "What feedback loops will you create?"
                        ],
                        "priority": "important"
                    }
                }
            }
        }
        return templates.get(paradigm, {})
    
    def generate_questions(
        self, 
        paradigm: Paradigm,
        idea_id: str,
        entities: ExtractedEntities,
        research_context: Optional[ResearchContext] = None
    ) -> QuestionSet:
        """Generate paradigm-specific questions based on entities and research context."""
        
        template = self.paradigm_templates.get(paradigm)
        if not template:
            raise ValueError(f"No template found for paradigm: {paradigm}")
        
        questions = []
        
        # Generate questions for each category
        for category, category_data in template.get("question_categories", {}).items():
            category_questions = self._generate_category_questions(
                paradigm=paradigm,
                category=category,
                category_data=category_data,
                entities=entities,
                research_context=research_context
            )
            questions.extend(category_questions)
        
        # Generate adaptive questions based on gaps
        adaptive_questions = self._generate_adaptive_questions(
            paradigm=paradigm,
            entities=entities,
            research_context=research_context
        )
        questions.extend(adaptive_questions)
        
        # Prioritize and classify questions
        questions = self._prioritize_and_classify_questions(questions, entities)
        
        return QuestionSet(
            paradigm=paradigm,
            idea_id=idea_id,
            questions=questions,
            total_critical_questions=len([q for q in questions if q.priority == QuestionPriority.CRITICAL])
        )
    
    def _generate_category_questions(
        self,
        paradigm: Paradigm,
        category: str,
        category_data: Dict[str, Any],
        entities: ExtractedEntities,
        research_context: Optional[ResearchContext]
    ) -> List[Question]:
        """Generate questions for a specific category."""
        
        questions = []
        base_questions = category_data.get("questions", [])
        priority = QuestionPriority(category_data.get("priority", "important"))
        
        for question_text in base_questions:
            # Contextualize question based on entities
            contextualized_question = self._contextualize_question(
                question_text, entities, research_context
            )
            
            question = Question(
                text=contextualized_question,
                paradigm=paradigm,
                category=category,
                priority=priority,
                question_type=self._classify_question_type(contextualized_question),
                context={
                    "base_question": question_text,
                    "category": category,
                    "entities_available": list(entities.dict().keys())
                },
                related_entities=self._identify_related_entities(contextualized_question, entities)
            )
            
            questions.append(question)
        
        return questions
    
    def _generate_adaptive_questions(
        self,
        paradigm: Paradigm,
        entities: ExtractedEntities,
        research_context: Optional[ResearchContext]
    ) -> List[Question]:
        """Generate adaptive questions based on identified gaps in entities/research."""
        
        adaptive_questions = []
        
        # Check for missing critical entities
        if not entities.problems:
            adaptive_questions.append(Question(
                text="What specific problem does your idea solve? Be as concrete as possible.",
                paradigm=paradigm,
                category="problem_identification",
                priority=QuestionPriority.CRITICAL,
                question_type=QuestionType.HUMAN_REQUIRED,
                context={"reason": "no_problems_identified"}
            ))
        
        if not entities.icps:
            adaptive_questions.append(Question(
                text="Who is your ideal customer? Describe them in detail including demographics, behaviors, and pain points.",
                paradigm=paradigm,
                category="icp_definition", 
                priority=QuestionPriority.CRITICAL,
                question_type=QuestionType.HUMAN_REQUIRED,
                context={"reason": "no_icp_identified"}
            ))
        
        # Check for low confidence entities
        low_confidence_entities = [
            entity for entity_list in [entities.problems, entities.assumptions, entities.constraints]
            for entity in entity_list
            if hasattr(entity, 'confidence') and entity.confidence < 0.6
        ]
        
        if low_confidence_entities:
            adaptive_questions.append(Question(
                text=f"Can you provide more details or validation for these aspects: {', '.join([str(e) for e in low_confidence_entities[:3]])}?",
                paradigm=paradigm,
                category="confidence_improvement",
                priority=QuestionPriority.IMPORTANT,
                question_type=QuestionType.HUMAN_REQUIRED,
                context={"low_confidence_entities": [str(e) for e in low_confidence_entities]}
            ))
        
        # Research-based questions
        if research_context and research_context.competitors:
            competitors_text = ", ".join([c.name for c in research_context.competitors[:3]])
            adaptive_questions.append(Question(
                text=f"We found these competitors: {competitors_text}. How will you differentiate from them?",
                paradigm=paradigm,
                category="competitive_analysis",
                priority=QuestionPriority.IMPORTANT,
                question_type=QuestionType.HUMAN_REQUIRED,
                context={"competitors_found": [c.dict() for c in research_context.competitors]}
            ))
        
        return adaptive_questions
    
    def _contextualize_question(
        self, 
        question_text: str, 
        entities: ExtractedEntities,
        research_context: Optional[ResearchContext]
    ) -> str:
        """Add context to generic questions based on available entities and research."""
        
        # Add problem context if available
        if entities.problems and "{problem}" in question_text:
            primary_problem = entities.problems[0]
            question_text = question_text.replace("{problem}", str(primary_problem.statement))
        
        # Add ICP context if available
        if entities.icps and "{icp}" in question_text:
            primary_icp = entities.icps[0]
            question_text = question_text.replace("{icp}", primary_icp.segment)
        
        # Add market context from research
        if research_context and research_context.market_data and "{market}" in question_text:
            market_size = research_context.market_data.get("size", "unknown")
            question_text = question_text.replace("{market}", f"${market_size}")
        
        return question_text
    
    def _classify_question_type(self, question_text: str) -> QuestionType:
        """Classify whether question requires human input, LLM can answer, or research can answer."""
        
        human_indicators = [
            "your experience", "your opinion", "you believe", "your strategy",
            "your competitive advantage", "your vision", "your budget", "your team",
            "your timeline", "what do you", "how do you", "why do you"
        ]
        
        research_indicators = [
            "market size", "competitors", "industry trends", "regulatory requirements",
            "pricing benchmarks", "technology alternatives", "industry standards"
        ]
        
        question_lower = question_text.lower()
        
        if any(indicator in question_lower for indicator in human_indicators):
            return QuestionType.HUMAN_REQUIRED
        elif any(indicator in question_lower for indicator in research_indicators):
            return QuestionType.RESEARCH_ANSWERABLE
        else:
            return QuestionType.LLM_ANSWERABLE
    
    def _identify_related_entities(
        self, 
        question_text: str, 
        entities: ExtractedEntities
    ) -> List[str]:
        """Identify which entities are related to this question."""
        
        related = []
        question_lower = question_text.lower()
        
        # Check problems
        for problem in entities.problems:
            if any(word in question_lower for word in problem.statement.lower().split()[:5]):
                related.append(problem.id)
        
        # Check ICPs  
        for icp in entities.icps:
            if any(word in question_lower for word in icp.segment.lower().split()[:3]):
                related.append(icp.id)
        
        # Check assumptions
        for assumption in entities.assumptions:
            if "assumption" in question_lower or "believe" in question_lower:
                related.append(assumption.id)
        
        return related
    
    def _prioritize_and_classify_questions(
        self, 
        questions: List[Question],
        entities: ExtractedEntities
    ) -> List[Question]:
        """Sort questions by priority and add confidence/suggestions where possible."""
        
        # Sort by priority (critical first, then important, then nice-to-have)
        priority_order = {
            QuestionPriority.CRITICAL: 0,
            QuestionPriority.IMPORTANT: 1, 
            QuestionPriority.NICE_TO_HAVE: 2
        }
        
        questions.sort(key=lambda q: (priority_order[q.priority], q.category))
        
        return questions
    
    async def generate_llm_suggestions(
        self, 
        questions: List[Question],
        entities: ExtractedEntities,
        research_context: Optional[ResearchContext] = None
    ) -> List[Question]:
        """Generate LLM suggestions for answerable questions."""
        
        for question in questions:
            if question.question_type in [QuestionType.LLM_ANSWERABLE, QuestionType.RESEARCH_ANSWERABLE]:
                try:
                    suggestion = await self._generate_single_suggestion(
                        question, entities, research_context
                    )
                    question.suggested_answer = suggestion["answer"]
                    question.confidence = suggestion["confidence"]
                except Exception as e:
                    logger.error(f"Failed to generate suggestion for question {question.id}: {e}")
        
        return questions
    
    async def _generate_single_suggestion(
        self,
        question: Question,
        entities: ExtractedEntities, 
        research_context: Optional[ResearchContext]
    ) -> Dict[str, Any]:
        """Generate a single LLM suggestion for a question."""
        
        context_prompt = f"""
        Based on the following context, provide a thoughtful answer to this question.
        
        Question: {question.text}
        Category: {question.category}
        Paradigm: {question.paradigm.value}
        
        Available Context:
        - Problems: {[p.statement for p in entities.problems]}
        - Target Users: {[icp.segment for icp in entities.icps]}
        - Assumptions: {[a.statement for a in entities.assumptions]}
        - Constraints: {[c.description for c in entities.constraints]}
        """
        
        if research_context:
            context_prompt += f"""
        - Market Research: {research_context.summary if hasattr(research_context, 'summary') else 'Available'}
        - Competitors: {[c.name for c in research_context.competitors] if research_context.competitors else []}
            """
        
        context_prompt += """
        
        Provide a specific, actionable answer. Include your confidence level (0.0-1.0).
        Respond in JSON format:
        {
            "answer": "your suggested answer",
            "confidence": 0.85,
            "reasoning": "brief explanation of your reasoning"
        }
        """
        
        response = await self.multi_model.call_model(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": context_prompt}],
            response_format="json"
        )
        
        return response
    
    def create_review_session(
        self, 
        question_set: QuestionSet,
        session_config: Optional[Dict[str, Any]] = None
    ) -> ReviewSession:
        """Create a human review session for questions."""
        
        # Separate questions by type
        human_questions = [
            q.id for q in question_set.questions 
            if q.question_type == QuestionType.HUMAN_REQUIRED
        ]
        
        # Prioritize critical questions first
        critical_questions = [
            q.id for q in question_set.questions
            if q.priority == QuestionPriority.CRITICAL
        ]
        
        # Order questions: critical human-required first, then other critical, then important
        ordered_questions = []
        for q in question_set.questions:
            if q.priority == QuestionPriority.CRITICAL and q.question_type == QuestionType.HUMAN_REQUIRED:
                ordered_questions.append(q.id)
        
        for q in question_set.questions:
            if q.id not in ordered_questions and q.priority == QuestionPriority.CRITICAL:
                ordered_questions.append(q.id)
        
        for q in question_set.questions:
            if q.id not in ordered_questions and q.priority == QuestionPriority.IMPORTANT:
                ordered_questions.append(q.id)
        
        for q in question_set.questions:
            if q.id not in ordered_questions:
                ordered_questions.append(q.id)
        
        return ReviewSession(
            question_set_id=question_set.idea_id,
            pending_questions=ordered_questions,
            session_data={
                "total_questions": len(question_set.questions),
                "critical_questions": len(critical_questions),
                "human_required": len(human_questions),
                "paradigm": question_set.paradigm.value,
                **(session_config or {})
            }
        )
    
    def update_question_answer(
        self,
        question_id: str,
        answer: str,
        rationale: Optional[str] = None,
        human_override: bool = False
    ) -> Question:
        """Update question with human answer and rationale."""
        
        # In a real implementation, this would update the database
        # For now, we return a mock updated question
        question = Question(
            id=question_id,
            text="mock question",
            paradigm=Paradigm.YC,
            category="mock",
            priority=QuestionPriority.IMPORTANT,
            question_type=QuestionType.HUMAN_REQUIRED,
            human_answer=answer,
            answer_rationale=rationale,
            answered_at=datetime.utcnow()
        )
        
        # Update in Neo4j graph
        self._store_question_answer(question)
        
        return question
    
    def _store_question_answer(self, question: Question) -> None:
        """Store question answer in Neo4j graph."""
        
        # Create or update question node
        query = """
        MERGE (q:Question {id: $question_id})
        SET q.text = $text,
            q.category = $category,
            q.priority = $priority,
            q.question_type = $question_type,
            q.paradigm = $paradigm,
            q.human_answer = $human_answer,
            q.answer_rationale = $rationale,
            q.answered_at = datetime(),
            q.updated_at = datetime()
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            session.run(query, {
                "question_id": question.id,
                "text": question.text,
                "category": question.category,
                "priority": question.priority.value,
                "question_type": question.question_type.value,
                "paradigm": question.paradigm.value,
                "human_answer": question.human_answer,
                "rationale": question.answer_rationale
            })
    
    def get_completion_status(self, question_set_id: str) -> Dict[str, Any]:
        """Get completion status for a question set."""
        
        # Query Neo4j for question completion status
        query = """
        MATCH (q:Question)
        WHERE q.question_set_id = $question_set_id
        WITH count(q) as total,
             sum(CASE WHEN q.human_answer IS NOT NULL OR q.suggested_answer IS NOT NULL THEN 1 ELSE 0 END) as answered,
             sum(CASE WHEN q.priority = 'critical' THEN 1 ELSE 0 END) as critical_total,
             sum(CASE WHEN q.priority = 'critical' AND (q.human_answer IS NOT NULL OR q.suggested_answer IS NOT NULL) THEN 1 ELSE 0 END) as critical_answered
        RETURN {
            total_questions: total,
            answered_questions: answered,
            completion_rate: CASE WHEN total > 0 THEN toFloat(answered) / total ELSE 0.0 END,
            critical_completion_rate: CASE WHEN critical_total > 0 THEN toFloat(critical_answered) / critical_total ELSE 1.0 END,
            ready_for_next_stage: CASE WHEN critical_total > 0 THEN critical_answered = critical_total ELSE false END
        } as status
        """
        
        with self.neo4j.driver.session(database=self.neo4j.config.database) as session:
            result = session.run(query, {"question_set_id": question_set_id})
            record = result.single()
            return record["status"] if record else {
                "total_questions": 0,
                "answered_questions": 0, 
                "completion_rate": 0.0,
                "critical_completion_rate": 0.0,
                "ready_for_next_stage": False
            }
