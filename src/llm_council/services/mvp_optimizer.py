"""MVP optimization and WSJF prioritization algorithms."""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import heapq

from ..models.se_models import (
    SEEntity, SERelationship, SEContextGraph, MVPCutResult, 
    WSJFMetrics, Stage, ArtifactLayer
)


@dataclass
class OptimizationConstraints:
    """Constraints for MVP optimization."""
    max_budget: float
    max_risk: float
    min_value_threshold: float
    required_entities: List[str]  # Must-have entities for end-to-end flow
    excluded_entities: List[str]  # Explicitly excluded entities


class MVPOptimizer:
    """Optimizes entity selection for MVP using value/risk/cost analysis."""
    
    def __init__(self):
        self.alpha = 1.0  # Risk penalty weight
        self.beta = 1.0   # Cost penalty weight
    
    def optimize_mvp_cut(self, graph: SEContextGraph, 
                        constraints: OptimizationConstraints) -> MVPCutResult:
        """
        Solve MVP optimization problem:
        maximize Σ Payoff_i 
        subject to Σ Cost_i ≤ Budget, Risk_total ≤ R_max, deps satisfied
        """
        
        # Calculate payoff scores for all entities
        entity_scores = self._calculate_entity_payoffs(graph)
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(graph)
        
        # Solve constrained optimization
        selected_entities, deferred_entities = self._solve_knapsack_with_deps(
            entity_scores, dependency_graph, constraints
        )
        
        # Calculate totals for selected set
        totals = self._calculate_totals(selected_entities, graph)
        
        # Assess feasibility
        feasibility = self._assess_feasibility(selected_entities, graph, constraints)
        
        return MVPCutResult(
            selected_entities=[e.id for e in selected_entities],
            deferred_entities=[e.id for e in deferred_entities],
            total_value=totals["value"],
            total_risk=totals["risk"],
            total_cost=totals["cost"],
            feasibility_score=feasibility
        )
    
    def _calculate_entity_payoffs(self, graph: SEContextGraph) -> Dict[str, float]:
        """Calculate payoff scores for all entities."""
        scores = {}
        
        for entity in graph.entities:
            if entity.se_meta:
                payoff = entity.se_meta.payoff_score(self.alpha, self.beta)
                # Adjust for importance and certainty
                adjusted_payoff = payoff * entity.importance * entity.certainty
                scores[entity.id] = adjusted_payoff
            else:
                # Fallback scoring for entities without SE metadata
                scores[entity.id] = entity.importance * entity.certainty
        
        return scores
    
    def _build_dependency_graph(self, graph: SEContextGraph) -> Dict[str, List[str]]:
        """Build dependency mapping from relationships."""
        deps = {entity.id: [] for entity in graph.entities}
        
        for rel in graph.relationships:
            if rel.type in ["requires", "depends_on"]:
                deps[rel.target_id].append(rel.source_id)
        
        return deps
    
    def _solve_knapsack_with_deps(self, entity_scores: Dict[str, float],
                                 dependency_graph: Dict[str, List[str]],
                                 constraints: OptimizationConstraints) -> Tuple[List[SEEntity], List[SEEntity]]:
        """Solve constrained knapsack with dependency satisfaction."""
        
        # Start with required entities
        selected_ids = set(constraints.required_entities)
        
        # Add dependencies of required entities
        self._add_transitive_dependencies(selected_ids, dependency_graph)
        
        # Remove excluded entities
        selected_ids -= set(constraints.excluded_entities)
        
        # Greedy selection of remaining entities by payoff/cost ratio
        remaining_entities = [
            entity_id for entity_id in entity_scores.keys() 
            if entity_id not in selected_ids and entity_id not in constraints.excluded_entities
        ]
        
        # Sort by payoff score descending
        remaining_entities.sort(key=lambda eid: entity_scores[eid], reverse=True)
        
        # Add entities while constraints are satisfied
        current_cost = self._calculate_cost_subset(selected_ids)
        current_risk = self._calculate_risk_subset(selected_ids)
        
        for entity_id in remaining_entities:
            # Check if adding this entity violates constraints
            entity_cost = self._get_entity_cost(entity_id)
            entity_risk = self._get_entity_risk(entity_id)
            
            if (current_cost + entity_cost <= constraints.max_budget and
                current_risk + entity_risk <= constraints.max_risk and
                entity_scores[entity_id] >= constraints.min_value_threshold):
                
                selected_ids.add(entity_id)
                # Add dependencies
                self._add_transitive_dependencies(selected_ids, dependency_graph)
                
                current_cost = self._calculate_cost_subset(selected_ids)
                current_risk = self._calculate_risk_subset(selected_ids)
        
        # Split into selected and deferred based on final selection
        # Note: This is a simplified implementation - actual implementation would need access to full entities
        selected_entities = []  # Would map IDs back to entities
        deferred_entities = []  # Would map remaining IDs to entities
        
        return selected_entities, deferred_entities
    
    def _add_transitive_dependencies(self, selected_ids: set, dependency_graph: Dict[str, List[str]]):
        """Add all transitive dependencies to selection."""
        added = True
        while added:
            added = False
            for entity_id in list(selected_ids):
                for dep_id in dependency_graph.get(entity_id, []):
                    if dep_id not in selected_ids:
                        selected_ids.add(dep_id)
                        added = True
    
    def _calculate_cost_subset(self, entity_ids: set) -> float:
        """Calculate total cost for entity subset."""
        # Implementation would sum costs from actual entities
        return 0.0  # Placeholder
    
    def _calculate_risk_subset(self, entity_ids: set) -> float:
        """Calculate total risk for entity subset."""
        # Implementation would aggregate risks from actual entities
        return 0.0  # Placeholder
    
    def _get_entity_cost(self, entity_id: str) -> float:
        """Get cost for specific entity."""
        # Implementation would lookup from entity metadata
        return 0.0  # Placeholder
    
    def _get_entity_risk(self, entity_id: str) -> float:
        """Get risk for specific entity."""
        # Implementation would lookup from entity metadata
        return 0.0  # Placeholder
    
    def _calculate_totals(self, entities: List[SEEntity], graph: SEContextGraph) -> Dict[str, float]:
        """Calculate total value, risk, cost for entity set."""
        totals = {"value": 0.0, "risk": 0.0, "cost": 0.0}
        
        for entity in entities:
            if entity.se_meta:
                if entity.se_meta.value_metrics:
                    totals["value"] += entity.se_meta.value_metrics.total_value
                if entity.se_meta.risk_metrics:
                    totals["risk"] += entity.se_meta.risk_metrics.total_risk
                if entity.se_meta.cost_data:
                    totals["cost"] += (entity.se_meta.cost_data.one_time + 
                                     entity.se_meta.cost_data.monthly * 12)
        
        return totals
    
    def _assess_feasibility(self, entities: List[SEEntity], graph: SEContextGraph,
                          constraints: OptimizationConstraints) -> float:
        """Assess overall feasibility of MVP scope."""
        if not entities:
            return 0.0
        
        # Factors affecting feasibility
        dependency_completeness = self._check_dependency_completeness(entities, graph)
        resource_fit = self._check_resource_constraints(entities, constraints)
        complexity_score = self._assess_complexity(entities)
        
        # Weighted feasibility score
        feasibility = (
            0.4 * dependency_completeness +
            0.3 * resource_fit +
            0.3 * (1.0 - complexity_score)  # Lower complexity = higher feasibility
        )
        
        return min(1.0, max(0.0, feasibility))
    
    def _check_dependency_completeness(self, entities: List[SEEntity], graph: SEContextGraph) -> float:
        """Check if all dependencies are included in selection."""
        entity_ids = {e.id for e in entities}
        missing_deps = 0
        total_deps = 0
        
        for rel in graph.relationships:
            if rel.type in ["requires", "depends_on"] and rel.target_id in entity_ids:
                total_deps += 1
                if rel.source_id not in entity_ids:
                    missing_deps += 1
        
        return 1.0 - (missing_deps / max(1, total_deps))
    
    def _check_resource_constraints(self, entities: List[SEEntity], 
                                  constraints: OptimizationConstraints) -> float:
        """Check how well selection fits within resource constraints."""
        totals = self._calculate_totals(entities, SEContextGraph(entities, [], "", 0.0))
        
        budget_utilization = totals["cost"] / max(1, constraints.max_budget)
        risk_utilization = totals["risk"] / max(1, constraints.max_risk)
        
        # Penalize over-utilization, reward efficient utilization
        budget_score = 1.0 if budget_utilization <= 1.0 else 1.0 / budget_utilization
        risk_score = 1.0 if risk_utilization <= 1.0 else 1.0 / risk_utilization
        
        return (budget_score + risk_score) / 2.0
    
    def _assess_complexity(self, entities: List[SEEntity]) -> float:
        """Assess implementation complexity of entity set."""
        if not entities:
            return 0.0
        
        complexity_factors = []
        
        for entity in entities:
            # Base complexity from entity importance (higher importance often = more complex)
            base_complexity = entity.importance
            
            # Adjust for uncertainty (higher uncertainty = higher complexity)
            uncertainty_penalty = 1.0 - entity.certainty
            
            # SE metadata complexity indicators
            if entity.se_meta and entity.se_meta.cost_data:
                # Higher effort points indicate complexity
                effort_factor = min(1.0, entity.se_meta.cost_data.effort_points / 100.0) if entity.se_meta.cost_data.effort_points else 0.0
                entity_complexity = (base_complexity + uncertainty_penalty + effort_factor) / 3.0
            else:
                entity_complexity = (base_complexity + uncertainty_penalty) / 2.0
            
            complexity_factors.append(entity_complexity)
        
        return sum(complexity_factors) / len(complexity_factors)


class WSJFPrioritizer:
    """Weighted Shortest Job First prioritization for implementation planning."""
    
    def prioritize_entities(self, entities: List[SEEntity]) -> List[Tuple[SEEntity, float]]:
        """Prioritize entities using WSJF scoring."""
        scored_entities = []
        
        for entity in entities:
            if entity.se_meta and entity.se_meta.wsjf_metrics:
                wsjf_score = entity.se_meta.wsjf_metrics.wsjf_score
                scored_entities.append((entity, wsjf_score))
            else:
                # Fallback WSJF calculation from basic metrics
                fallback_score = self._calculate_fallback_wsjf(entity)
                scored_entities.append((entity, fallback_score))
        
        # Sort by WSJF score descending (highest priority first)
        scored_entities.sort(key=lambda x: x[1], reverse=True)
        
        return scored_entities
    
    def _calculate_fallback_wsjf(self, entity: SEEntity) -> float:
        """Calculate fallback WSJF score from basic entity attributes."""
        # Use importance as business value proxy
        business_value = entity.importance * 10.0
        
        # Use (1 - certainty) as time criticality proxy (uncertain = urgent to validate)
        time_criticality = (1.0 - entity.certainty) * 10.0
        
        # Use importance as risk reduction proxy
        risk_reduction = entity.importance * 10.0
        
        # Use inverse importance as effort proxy (high importance = likely complex)
        effort = max(1.0, (1.0 - entity.importance) * 10.0 + 1.0)
        
        return (business_value + time_criticality + risk_reduction) / effort
    
    def generate_sprint_plan(self, prioritized_entities: List[Tuple[SEEntity, float]], 
                           sprint_capacity: float = 40.0) -> Dict[str, List[str]]:
        """Generate sprint allocation based on WSJF priorities and capacity."""
        sprints = {}
        current_sprint = 1
        current_capacity = 0.0
        current_sprint_entities = []
        
        for entity, wsjf_score in prioritized_entities:
            # Estimate effort (simplified)
            entity_effort = self._estimate_entity_effort(entity)
            
            # Check if entity fits in current sprint
            if current_capacity + entity_effort <= sprint_capacity:
                current_sprint_entities.append(entity.id)
                current_capacity += entity_effort
            else:
                # Close current sprint and start new one
                if current_sprint_entities:
                    sprints[f"Sprint {current_sprint}"] = current_sprint_entities
                    current_sprint += 1
                    current_sprint_entities = [entity.id]
                    current_capacity = entity_effort
        
        # Add final sprint if it has entities
        if current_sprint_entities:
            sprints[f"Sprint {current_sprint}"] = current_sprint_entities
        
        return sprints
    
    def _estimate_entity_effort(self, entity: SEEntity) -> float:
        """Estimate implementation effort for entity."""
        if (entity.se_meta and entity.se_meta.cost_data and 
            entity.se_meta.cost_data.effort_points):
            return entity.se_meta.cost_data.effort_points
        
        # Fallback effort estimation
        base_effort = entity.importance * 20.0  # High importance = more effort
        uncertainty_penalty = (1.0 - entity.certainty) * 10.0  # Uncertainty adds effort
        
        return max(1.0, base_effort + uncertainty_penalty)


class CriticalPathAnalyzer:
    """Analyzes critical path through entity dependencies."""
    
    def find_critical_path(self, entities: List[SEEntity], 
                         relationships: List[SERelationship]) -> List[str]:
        """Find critical path through entity dependencies."""
        
        # Build adjacency list for dependency graph
        graph = {entity.id: [] for entity in entities}
        effort_map = {entity.id: self._get_entity_effort(entity) for entity in entities}
        
        for rel in relationships:
            if rel.type in ["requires", "depends_on", "enables"]:
                graph[rel.source_id].append((rel.target_id, effort_map[rel.target_id]))
        
        # Find longest path (critical path) using topological sort + longest path
        return self._longest_path(graph, effort_map)
    
    def _get_entity_effort(self, entity: SEEntity) -> float:
        """Get effort estimate for entity."""
        if (entity.se_meta and entity.se_meta.cost_data and 
            entity.se_meta.cost_data.effort_points):
            return entity.se_meta.cost_data.effort_points
        
        return entity.importance * 10.0  # Fallback
    
    def _longest_path(self, graph: Dict[str, List[Tuple[str, float]]], 
                     effort_map: Dict[str, float]) -> List[str]:
        """Find longest path in DAG (critical path)."""
        
        # Topological sort
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for neighbor, _ in graph[node]:
                in_degree[neighbor] += 1
        
        # Queue of nodes with no incoming edges
        queue = [node for node in in_degree if in_degree[node] == 0]
        topo_order = []
        
        while queue:
            node = queue.pop(0)
            topo_order.append(node)
            
            for neighbor, _ in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Find longest path using dynamic programming
        dist = {node: 0.0 for node in graph}
        parent = {node: None for node in graph}
        
        for node in topo_order:
            for neighbor, weight in graph[node]:
                if dist[node] + weight > dist[neighbor]:
                    dist[neighbor] = dist[node] + weight
                    parent[neighbor] = node
        
        # Reconstruct longest path
        max_node = max(dist.keys(), key=lambda x: dist[x])
        path = []
        current = max_node
        
        while current is not None:
            path.append(current)
            current = parent[current]
        
        return list(reversed(path))


class StageClassifier:
    """Classifies entities into development stages (MVP/V1/V2)."""
    
    def classify_entities_by_stage(self, mvp_cut: MVPCutResult, 
                                 all_entities: List[SEEntity]) -> Dict[Stage, List[str]]:
        """Classify all entities into development stages."""
        
        classification = {
            Stage.MVP: mvp_cut.selected_entities,
            Stage.V1: [],
            Stage.V2: [],
            Stage.BACKLOG: [],
            Stage.CUT: []
        }
        
        # Classify deferred entities by priority
        deferred_with_scores = []
        for entity_id in mvp_cut.deferred_entities:
            entity = next((e for e in all_entities if e.id == entity_id), None)
            if entity:
                score = self._calculate_priority_score(entity)
                deferred_with_scores.append((entity_id, score))
        
        # Sort by priority score
        deferred_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign to stages based on priority tiers
        total_deferred = len(deferred_with_scores)
        v1_cutoff = int(total_deferred * 0.3)  # Top 30% → V1
        v2_cutoff = int(total_deferred * 0.7)  # Next 40% → V2, Bottom 30% → Backlog
        
        for i, (entity_id, score) in enumerate(deferred_with_scores):
            if i < v1_cutoff:
                classification[Stage.V1].append(entity_id)
            elif i < v2_cutoff:
                classification[Stage.V2].append(entity_id)
            else:
                classification[Stage.BACKLOG].append(entity_id)
        
        return classification
    
    def _calculate_priority_score(self, entity: SEEntity) -> float:
        """Calculate priority score for stage classification."""
        base_score = entity.importance * entity.certainty
        
        if entity.se_meta:
            # Boost score based on value metrics
            if entity.se_meta.value_metrics:
                value_boost = entity.se_meta.value_metrics.total_value * 0.3
                base_score += value_boost
            
            # Reduce score based on risk and cost
            if entity.se_meta.risk_metrics:
                risk_penalty = entity.se_meta.risk_metrics.total_risk * 0.2
                base_score -= risk_penalty
            
            if entity.se_meta.cost_data:
                cost_penalty = min(0.3, entity.se_meta.cost_data.one_time / 10000.0)
                base_score -= cost_penalty
        
        return max(0.0, base_score)


class MVPValidator:
    """Validates MVP cuts for completeness and coherence."""
    
    def validate_mvp_cut(self, mvp_cut: MVPCutResult, graph: SEContextGraph) -> Dict[str, Any]:
        """Validate MVP cut for end-to-end completeness."""
        
        validation_results = {
            "is_valid": True,
            "issues": [],
            "recommendations": [],
            "completeness_score": 0.0
        }
        
        # Check for end-to-end user flow completeness
        flow_completeness = self._validate_user_flow(mvp_cut, graph)
        validation_results["completeness_score"] = flow_completeness
        
        if flow_completeness < 0.8:
            validation_results["is_valid"] = False
            validation_results["issues"].append(
                f"Incomplete user flow (score: {flow_completeness:.1f}/1.0)"
            )
        
        # Check for critical missing dependencies
        missing_deps = self._find_missing_dependencies(mvp_cut, graph)
        if missing_deps:
            validation_results["issues"].extend(
                [f"Missing dependency: {dep}" for dep in missing_deps]
            )
        
        # Check for value/cost balance
        if mvp_cut.total_cost > 0 and mvp_cut.total_value / mvp_cut.total_cost < 1.5:
            validation_results["issues"].append(
                "Low value/cost ratio - consider reducing scope or adding value"
            )
        
        # Generate recommendations
        if validation_results["issues"]:
            validation_results["recommendations"] = self._generate_recommendations(
                validation_results["issues"], mvp_cut, graph
            )
        
        return validation_results
    
    def _validate_user_flow(self, mvp_cut: MVPCutResult, graph: SEContextGraph) -> float:
        """Validate that MVP includes complete user flow."""
        selected_ids = set(mvp_cut.selected_entities)
        
        # Look for user flow entities in selection
        user_flow_types = ["user_group", "problem", "solution", "feature"]
        flow_coverage = 0.0
        
        for entity in graph.entities:
            if entity.id in selected_ids and entity.type in user_flow_types:
                flow_coverage += 0.25  # Each type adds 25% coverage
        
        return min(1.0, flow_coverage)
    
    def _find_missing_dependencies(self, mvp_cut: MVPCutResult, 
                                 graph: SEContextGraph) -> List[str]:
        """Find critical dependencies missing from MVP selection."""
        selected_ids = set(mvp_cut.selected_entities)
        missing = []
        
        for rel in graph.relationships:
            if (rel.type in ["requires", "depends_on"] and 
                rel.target_id in selected_ids and 
                rel.source_id not in selected_ids):
                # Find the missing dependency entity
                missing_entity = next(
                    (e for e in graph.entities if e.id == rel.source_id), None
                )
                if missing_entity:
                    missing.append(missing_entity.label)
        
        return missing
    
    def _generate_recommendations(self, issues: List[str], mvp_cut: MVPCutResult, 
                                graph: SEContextGraph) -> List[str]:
        """Generate actionable recommendations to fix validation issues."""
        recommendations = []
        
        for issue in issues:
            if "Incomplete user flow" in issue:
                recommendations.append(
                    "Add missing user flow entities: ensure problem → solution → user outcome is complete"
                )
            elif "Missing dependency" in issue:
                recommendations.append(
                    "Review dependency graph and add critical dependencies to MVP scope"
                )
            elif "Low value/cost ratio" in issue:
                recommendations.append(
                    "Consider: 1) Remove low-value features, 2) Add high-value quick wins, 3) Reduce implementation complexity"
                )
        
        return recommendations