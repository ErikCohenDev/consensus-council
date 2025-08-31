"""Paradigm question engine for human-LLM collaboration."""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from ..models.se_models import ArtifactLayer, SEContextGraph, ParadigmQuestion, QuestionType
from ..human_review import HumanReviewInterface
from ..research_agent import ResearchAgent


# QuestionType and ParadigmQuestion are now imported from se_models


class ParadigmQuestionEngine:
    """Generates and manages paradigm questions throughout SE pipeline."""
    
    def __init__(self, human_review: HumanReviewInterface, research_agent: ResearchAgent):
        self.human_review = human_review
        self.research_agent = research_agent
        self.question_templates = self._load_question_templates()
    
    def _load_question_templates(self) -> Dict[ArtifactLayer, List[ParadigmQuestion]]:
        """Load paradigm question templates by artifact layer."""
        return {
            ArtifactLayer.VISION: [
                ParadigmQuestion(
                    id="vision_problem_clarity",
                    text="Is the core problem clearly defined and painful enough to pay for? Rate clarity 1-5 and explain.",
                    layer=ArtifactLayer.VISION,
                    question_type=QuestionType.HUMAN_REQUIRED,
                    weight=2.5,
                    rationale="Humans have better intuition for problem-market fit than LLMs",
                    research_triggers=["problem_market_research", "competitive_landscape"],
                    entity_tags=["core_problem", "target_audience"]
                ),
                ParadigmQuestion(
                    id="vision_audience_specificity",
                    text="Is the target audience specific enough? Describe your ideal customer persona.",
                    layer=ArtifactLayer.VISION,
                    question_type=QuestionType.HUMAN_PREFERRED,
                    weight=2.0,
                    rationale="Humans understand customer nuances and market segments better",
                    research_triggers=["demographic_research", "user_behavior_analysis"],
                    entity_tags=["target_audience", "user_personas"]
                ),
                ParadigmQuestion(
                    id="vision_budget_constraints",
                    text="What is the realistic budget range and timeline for this project?",
                    layer=ArtifactLayer.VISION,
                    question_type=QuestionType.HUMAN_ONLY,
                    weight=2.5,
                    rationale="Only humans know actual resource constraints and business context",
                    research_triggers=["cost_benchmarks", "development_timelines"],
                    entity_tags=["budget_constraints", "timeline_constraints"]
                ),
                ParadigmQuestion(
                    id="vision_success_definition",
                    text="How will you measure success? What are the key metrics and targets?",
                    layer=ArtifactLayer.VISION,
                    question_type=QuestionType.HUMAN_REQUIRED,
                    weight=2.2,
                    rationale="Success metrics require business strategy and competitive context",
                    research_triggers=["industry_benchmarks", "success_metrics_analysis"],
                    entity_tags=["success_metrics", "business_objectives"]
                )
            ],
            
            ArtifactLayer.PRD: [
                ParadigmQuestion(
                    id="prd_user_workflow",
                    text="Walk through the complete user workflow step-by-step. Where might users get stuck?",
                    layer=ArtifactLayer.PRD,
                    question_type=QuestionType.HUMAN_PREFERRED,
                    weight=2.0,
                    rationale="Humans catch workflow gaps and UX issues that LLMs miss",
                    research_triggers=["ux_best_practices", "user_journey_research"],
                    entity_tags=["user_workflows", "ux_requirements"]
                ),
                ParadigmQuestion(
                    id="prd_integration_requirements",
                    text="What existing systems/APIs/data sources must this integrate with?",
                    layer=ArtifactLayer.PRD,
                    question_type=QuestionType.HUMAN_ONLY,
                    weight=2.3,
                    rationale="Integration requirements depend on existing infrastructure context",
                    research_triggers=["integration_options", "api_documentation"],
                    entity_tags=["integrations", "data_requirements"]
                ),
                ParadigmQuestion(
                    id="prd_compliance_requirements",
                    text="Any regulatory, compliance, or security requirements (HIPAA, GDPR, SOC2)?",
                    layer=ArtifactLayer.PRD,
                    question_type=QuestionType.HYBRID,
                    weight=2.1,
                    rationale="LLM knows standards, human knows business applicability",
                    research_triggers=["compliance_research", "security_standards"],
                    entity_tags=["compliance_requirements", "security_controls"]
                )
            ],
            
            ArtifactLayer.ARCHITECTURE: [
                ParadigmQuestion(
                    id="arch_technology_constraints",
                    text="Any technology stack constraints, preferences, or existing infrastructure to leverage?",
                    layer=ArtifactLayer.ARCHITECTURE,
                    question_type=QuestionType.HUMAN_ONLY,
                    weight=1.8,
                    rationale="Team expertise and existing infrastructure constraints are context-specific",
                    research_triggers=["technology_options", "architecture_patterns"],
                    entity_tags=["technology_stack", "infrastructure_constraints"]
                ),
                ParadigmQuestion(
                    id="arch_scalability_requirements",
                    text="Expected user scale and growth trajectory? Performance requirements?",
                    layer=ArtifactLayer.ARCHITECTURE,
                    question_type=QuestionType.HYBRID,
                    weight=1.7,
                    rationale="LLM can estimate technical requirements, human validates business projections",
                    research_triggers=["scalability_patterns", "performance_benchmarks"],
                    entity_tags=["scalability_requirements", "performance_targets"]
                ),
                ParadigmQuestion(
                    id="arch_team_capabilities",
                    text="What are your team's technical strengths and learning constraints?",
                    layer=ArtifactLayer.ARCHITECTURE,
                    question_type=QuestionType.HUMAN_ONLY,
                    weight=1.9,
                    rationale="Team capabilities directly impact architectural decisions",
                    research_triggers=["technology_learning_curves", "team_productivity_research"],
                    entity_tags=["team_constraints", "technology_choices"]
                )
            ],
            
            ArtifactLayer.IMPLEMENTATION: [
                ParadigmQuestion(
                    id="impl_resource_allocation",
                    text="How many developers and what skill mix do you have available?",
                    layer=ArtifactLayer.IMPLEMENTATION,
                    question_type=QuestionType.HUMAN_ONLY,
                    weight=2.0,
                    rationale="Resource allocation requires actual team and budget knowledge",
                    research_triggers=["developer_productivity_metrics", "project_estimation"],
                    entity_tags=["resource_allocation", "team_capacity"]
                ),
                ParadigmQuestion(
                    id="impl_delivery_priorities",
                    text="What features are absolutely critical for launch vs nice-to-have?",
                    layer=ArtifactLayer.IMPLEMENTATION,
                    question_type=QuestionType.HUMAN_REQUIRED,
                    weight=2.3,
                    rationale="Business priorities and launch strategy require human judgment",
                    research_triggers=["mvp_feature_analysis", "launch_strategy_research"],
                    entity_tags=["mvp_features", "feature_priorities"]
                ),
                ParadigmQuestion(
                    id="impl_risk_tolerance",
                    text="What is your risk tolerance for technical debt vs speed to market?",
                    layer=ArtifactLayer.IMPLEMENTATION,
                    question_type=QuestionType.HUMAN_REQUIRED,
                    weight=1.8,
                    rationale="Risk tolerance is a strategic business decision",
                    research_triggers=["technical_debt_research", "speed_vs_quality_analysis"],
                    entity_tags=["technical_risks", "delivery_strategy"]
                )
            ]
        }
    
    async def generate_layer_questions(self, graph: SEContextGraph, 
                                     layer: ArtifactLayer) -> List[ParadigmQuestion]:
        """Generate contextual questions for specific artifact layer."""
        base_questions = self.question_templates.get(layer, [])
        
        # Filter questions based on graph entities and context
        relevant_questions = []
        for question in base_questions:
            # Check if question is relevant to current graph entities
            if self._is_question_relevant(question, graph):
                # Customize question text based on graph context
                customized = await self._customize_question(question, graph)
                relevant_questions.append(customized)
        
        return relevant_questions
    
    def _is_question_relevant(self, question: ParadigmQuestion, graph: SEContextGraph) -> bool:
        """Determine if question is relevant based on graph entities."""
        # Check if any entity tags match graph entity types/labels
        graph_types = {entity.type.lower() for entity in graph.entities}
        graph_labels = {entity.label.lower() for entity in graph.entities}
        
        for tag in question.entity_tags:
            tag_lower = tag.lower()
            if (tag_lower in graph_types or 
                any(tag_lower in label for label in graph_labels)):
                return True
        
        return True  # Include by default if no specific filtering
    
    async def _customize_question(self, question: ParadigmQuestion, 
                                graph: SEContextGraph) -> ParadigmQuestion:
        """Customize question text based on graph context."""
        # Find relevant entities
        relevant_entities = [
            entity for entity in graph.entities 
            if any(tag.lower() in entity.type.lower() or tag.lower() in entity.label.lower() 
                   for tag in question.entity_tags)
        ]
        
        if relevant_entities:
            # Add entity context to question
            entity_context = ", ".join([e.label for e in relevant_entities[:3]])
            customized_text = f"{question.text}\n\nContext: Your graph includes: {entity_context}"
            
            return ParadigmQuestion(
                id=question.id,
                text=customized_text,
                layer=question.layer,
                question_type=question.question_type,
                weight=question.weight,
                rationale=question.rationale,
                research_triggers=question.research_triggers,
                entity_tags=question.entity_tags
            )
        
        return question
    
    async def trigger_contextual_research(self, question: ParadigmQuestion, 
                                        graph: SEContextGraph) -> Dict[str, Any]:
        """Trigger research based on question's research triggers."""
        research_results = {}
        
        for trigger in question.research_triggers:
            try:
                # Generate research query based on graph context
                query = self._generate_research_query(trigger, graph, question)
                
                # Execute research
                results = await self.research_agent.search_and_synthesize(query, max_results=3)
                research_results[trigger] = results
                
            except Exception as e:
                print(f"Research failed for {trigger}: {e}")
                research_results[trigger] = None
        
        return research_results
    
    def _generate_research_query(self, trigger: str, graph: SEContextGraph, 
                               question: ParadigmQuestion) -> str:
        """Generate targeted research query based on trigger and graph context."""
        central_entity = next(
            (e for e in graph.entities if e.id == graph.central_entity_id), 
            None
        )
        
        if not central_entity:
            return f"{trigger} best practices"
        
        idea_context = central_entity.label.lower()
        
        query_templates = {
            "problem_market_research": f"{idea_context} market size and demand analysis",
            "competitive_landscape": f"{idea_context} competitive analysis and alternatives",
            "demographic_research": f"{idea_context} target user demographics and behavior",
            "user_behavior_analysis": f"{idea_context} user needs and pain points research",
            "cost_benchmarks": f"{idea_context} development cost estimates and benchmarks",
            "development_timelines": f"{idea_context} typical development timeline and milestones",
            "industry_benchmarks": f"{idea_context} industry success metrics and KPIs",
            "success_metrics_analysis": f"{idea_context} business model and revenue metrics",
            "ux_best_practices": f"{idea_context} user experience design patterns and best practices",
            "integration_options": f"{idea_context} API integration options and technical requirements",
            "compliance_research": f"{idea_context} regulatory compliance requirements and standards",
            "security_standards": f"{idea_context} security best practices and threat modeling",
            "technology_options": f"{idea_context} technology stack recommendations and comparisons",
            "architecture_patterns": f"{idea_context} software architecture patterns and scalability",
            "scalability_patterns": f"{idea_context} scalability challenges and solutions",
            "performance_benchmarks": f"{idea_context} performance requirements and optimization",
            "team_productivity_research": f"software development team productivity and estimation",
            "mvp_feature_analysis": f"{idea_context} minimum viable product feature prioritization",
            "launch_strategy_research": f"{idea_context} go-to-market strategy and launch best practices",
            "technical_debt_research": f"technical debt management and speed vs quality tradeoffs"
        }
        
        return query_templates.get(trigger, f"{trigger} {idea_context}")
    
    async def process_layer_with_paradigms(self, graph: SEContextGraph, 
                                         layer: ArtifactLayer) -> Dict[str, Any]:
        """Process artifact layer with paradigm questions and research expansion."""
        
        # Generate relevant questions for this layer
        questions = await self.generate_layer_questions(graph, layer)
        
        results = {
            "questions": [],
            "research_insights": {},
            "human_responses": {},
            "layer_confidence": 0.0
        }
        
        for question in questions:
            # Trigger contextual research first
            research = await self.trigger_contextual_research(question, graph)
            results["research_insights"][question.id] = research
            
            # Present question to human with research context
            if question.question_type in [QuestionType.HUMAN_ONLY, QuestionType.HUMAN_REQUIRED]:
                # Always require human input
                human_response = await self._get_human_response(question, research, graph)
                results["human_responses"][question.id] = human_response
                
            elif question.question_type == QuestionType.HUMAN_PREFERRED:
                # Try to get human input, fallback to LLM if needed
                human_response = await self._get_human_response_optional(question, research, graph)
                if human_response:
                    results["human_responses"][question.id] = human_response
                else:
                    # LLM fallback (implement LLM response generation)
                    pass
                    
            elif question.question_type == QuestionType.HYBRID:
                # Get LLM estimate first, then human validation
                llm_estimate = await self._get_llm_estimate(question, research, graph)
                human_validation = await self._get_human_validation(question, llm_estimate, research)
                results["human_responses"][question.id] = {
                    "llm_estimate": llm_estimate,
                    "human_validation": human_validation
                }
            
            results["questions"].append({
                "id": question.id,
                "text": question.text,
                "type": question.question_type.value,
                "weight": question.weight,
                "rationale": question.rationale
            })
        
        # Calculate layer confidence based on question responses
        results["layer_confidence"] = self._calculate_layer_confidence(questions, results)
        
        return results
    
    async def _get_human_response(self, question: ParadigmQuestion, 
                                research: Dict[str, Any], graph: SEContextGraph) -> str:
        """Get required human response to paradigm question."""
        
        # Format research context for human
        research_summary = self._format_research_for_human(research)
        
        # Present to human with full context
        prompt = f"""
{question.text}

Context from your project graph:
- Central idea: {next((e.label for e in graph.entities if e.id == graph.central_entity_id), 'Unknown')}
- Key entities: {', '.join([e.label for e in graph.entities[:5]])}

{research_summary}

Rationale: {question.rationale}
"""
        
        response = await self.human_review.get_human_input(
            prompt=prompt,
            context={"question_id": question.id, "layer": question.layer.value}
        )
        
        return response
    
    async def _get_human_response_optional(self, question: ParadigmQuestion,
                                         research: Dict[str, Any], graph: SEContextGraph) -> Optional[str]:
        """Get optional human response with timeout."""
        try:
            # Shorter timeout for optional questions
            return await self._get_human_response(question, research, graph)
        except TimeoutError:
            return None
    
    async def _get_llm_estimate(self, question: ParadigmQuestion,
                              research: Dict[str, Any], graph: SEContextGraph) -> str:
        """Get LLM estimate for hybrid questions."""
        # This would use the auditor worker to generate an estimate
        # Implementation would depend on available worker
        return "LLM estimate placeholder"
    
    async def _get_human_validation(self, question: ParadigmQuestion,
                                  llm_estimate: str, research: Dict[str, Any]) -> str:
        """Get human validation of LLM estimate."""
        validation_prompt = f"""
{question.text}

LLM Estimate: {llm_estimate}

Do you agree with this estimate? Please validate or provide corrections:
"""
        
        return await self.human_review.get_human_input(
            prompt=validation_prompt,
            context={"question_id": question.id, "validation_mode": True}
        )
    
    def _format_research_for_human(self, research: Dict[str, Any]) -> str:
        """Format research results for human consumption."""
        if not research:
            return "No research data available."
        
        formatted = ["Research Context:"]
        for trigger, data in research.items():
            if data:
                formatted.append(f"- {trigger.replace('_', ' ').title()}: {str(data)[:200]}...")
        
        return "\n".join(formatted)
    
    def _calculate_layer_confidence(self, questions: List[ParadigmQuestion], 
                                  results: Dict[str, Any]) -> float:
        """Calculate confidence score for artifact layer based on question responses."""
        if not questions:
            return 0.0
        
        total_weight = sum(q.weight for q in questions)
        answered_weight = 0.0
        
        for question in questions:
            if question.id in results["human_responses"]:
                response = results["human_responses"][question.id]
                # Score based on response completeness
                if isinstance(response, str) and len(response.strip()) > 20:
                    answered_weight += question.weight
                elif isinstance(response, dict) and response.get("human_validation"):
                    answered_weight += question.weight
        
        return answered_weight / total_weight if total_weight > 0 else 0.0


class LayerProjectionEngine:
    """Projects graph entities into artifact-specific views."""
    
    def __init__(self, paradigm_engine: ParadigmQuestionEngine):
        self.paradigm_engine = paradigm_engine
    
    async def project_to_layer(self, graph: SEContextGraph, 
                             layer: ArtifactLayer) -> Dict[str, Any]:
        """Project graph to specific artifact layer with human validation."""
        
        # Process paradigm questions for this layer
        paradigm_results = await self.paradigm_engine.process_layer_with_paradigms(graph, layer)
        
        # Filter entities and relationships relevant to this layer
        layer_entities = self._filter_entities_for_layer(graph.entities, layer)
        layer_relationships = self._filter_relationships_for_layer(
            graph.relationships, layer_entities, layer
        )
        
        # Generate artifact-specific focus areas
        focus_areas = self._generate_focus_areas(layer, paradigm_results)
        
        # Create decisions summary
        decisions = self._extract_decisions(paradigm_results)
        
        # Build traceability to upstream layers
        traceability = self._build_traceability(layer_entities, layer)
        
        return {
            "layer": layer.value,
            "entities": [entity.dict() for entity in layer_entities],
            "relationships": [rel.dict() for rel in layer_relationships],
            "focus_areas": focus_areas,
            "decisions": decisions,
            "traceability": traceability,
            "paradigm_results": paradigm_results,
            "confidence": paradigm_results["layer_confidence"]
        }
    
    def _filter_entities_for_layer(self, entities: List[Any], layer: ArtifactLayer) -> List[Any]:
        """Filter entities relevant to specific artifact layer."""
        layer_type_mapping = {
            ArtifactLayer.VISION: ["core_idea", "problem", "user_group", "market", "goal"],
            ArtifactLayer.PRD: ["feature", "requirement", "user_story", "acceptance_criteria"],
            ArtifactLayer.ARCHITECTURE: ["component", "interface", "service", "data_store", "security_control"],
            ArtifactLayer.IMPLEMENTATION: ["task", "milestone", "dependency", "test", "deployment"]
        }
        
        relevant_types = layer_type_mapping.get(layer, [])
        
        return [
            entity for entity in entities 
            if (entity.se_meta.layer == layer or 
                any(entity_type in entity.type.lower() for entity_type in relevant_types))
        ]
    
    def _filter_relationships_for_layer(self, relationships: List[Any], 
                                      entities: List[Any], layer: ArtifactLayer) -> List[Any]:
        """Filter relationships relevant to layer entities."""
        entity_ids = {entity.id for entity in entities}
        
        return [
            rel for rel in relationships 
            if rel.source_id in entity_ids and rel.target_id in entity_ids
        ]
    
    def _generate_focus_areas(self, layer: ArtifactLayer, paradigm_results: Dict[str, Any]) -> List[str]:
        """Generate focus areas based on layer type and paradigm responses."""
        focus_mapping = {
            ArtifactLayer.VISION: ["Problem Definition", "Target Market", "Value Proposition"],
            ArtifactLayer.PRD: ["User Experience", "Functional Requirements", "Success Metrics"],
            ArtifactLayer.ARCHITECTURE: ["System Design", "Technology Stack", "Security & Compliance"],
            ArtifactLayer.IMPLEMENTATION: ["Task Breakdown", "Resource Allocation", "Risk Management"]
        }
        
        return focus_mapping.get(layer, ["General Analysis"])
    
    def _extract_decisions(self, paradigm_results: Dict[str, Any]) -> List[str]:
        """Extract key decisions from paradigm question responses."""
        decisions = []
        
        for question_id, response in paradigm_results.get("human_responses", {}).items():
            if isinstance(response, str) and len(response.strip()) > 10:
                # Extract decision from response (simplified)
                decision = f"Decision for {question_id}: {response[:100]}..."
                decisions.append(decision)
        
        return decisions
    
    def _build_traceability(self, entities: List[Any], layer: ArtifactLayer) -> Dict[str, List[str]]:
        """Build traceability mapping to upstream layers."""
        # This would track which entities in this layer trace to entities in previous layers
        # Implementation would depend on entity relationships and layer history
        return {"upstream_entities": [entity.id for entity in entities]}


class ParadigmEngine:
    """Main paradigm engine combining question and projection engines."""
    
    def __init__(self, templates_dir: str = None):
        """Initialize paradigm engine with optional template directory."""
        from ..research_agent import ResearchAgent
        research_agent = ResearchAgent(enabled=False)  # Disable for testing
        self.question_engine = ParadigmQuestionEngine(research_agent, templates_dir)
        self.projection_engine = LayerProjectionEngine()
    
    async def execute_paradigm_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete paradigm analysis with human collaboration."""
        # Get paradigm questions
        questions = await self.question_engine.get_paradigm_questions(
            context.get("paradigm", "yc_startup"),
            context.get("layer", ArtifactLayer.VISION)
        )
        
        # Process responses (would involve human interaction in real implementation)
        responses = await self.question_engine.process_paradigm_responses(
            questions, context.get("responses", {})
        )
        
        # Generate layer projections
        projections = await self.projection_engine.generate_layer_projections(
            context, responses
        )
        
        return {
            "questions": questions,
            "responses": responses,
            "projections": projections,
            "paradigm_type": context.get("paradigm"),
            "layer": context.get("layer")
        }