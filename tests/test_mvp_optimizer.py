"""
Tests for MVP optimizer service.

VERIFIES: MVP scoping, resource optimization, and WSJF prioritization
VALIDATES: Resource constraints and feasibility analysis
TEST_TYPE: Unit + Integration  
LAST_SYNC: 2025-08-30
"""

import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime, timedelta

from src.llm_council.services.mvp_optimizer import MVPOptimizer
from src.llm_council.models.se_models import Feature, ResourceConstraints, WSJFMetrics


class TestMVPOptimizer:
    """Test MVP optimizer functionality and WSJF scoring."""
    
    def setup_method(self):
        """Set up test environment."""
        self.optimizer = MVPOptimizer()

    def test_wsjf_scoring_calculation(self):
        """
        VERIFIES: WSJF (Weighted Shortest Job First) scoring accuracy
        SCENARIO: Calculate WSJF scores for feature prioritization
        """
        # Step 1: Create features with WSJF metrics
        features = [
            Mock(
                id="F001",
                name="User Authentication", 
                wsjf_metrics=WSJFMetrics(
                    business_value=9,    # High business value
                    time_criticality=8,  # High urgency
                    risk_reduction=7,    # Medium risk reduction
                    effort=5             # Medium effort
                ),
                estimated_cost=8000,
                estimated_hours=80
            ),
            Mock(
                id="F002",
                name="Advanced Analytics",
                wsjf_metrics=WSJFMetrics(
                    business_value=6,    # Medium business value
                    time_criticality=3,  # Low urgency  
                    risk_reduction=4,    # Low risk reduction
                    effort=13            # High effort
                ),
                estimated_cost=25000,
                estimated_hours=200
            ),
            Mock(
                id="F003", 
                name="Basic Water Logging",
                wsjf_metrics=WSJFMetrics(
                    business_value=10,   # Highest business value
                    time_criticality=9,  # Very urgent
                    risk_reduction=8,    # High risk reduction
                    effort=3             # Low effort
                ),
                estimated_cost=3000,
                estimated_hours=30
            )
        ]
        
        # Step 2: Calculate WSJF scores
        scored_features = self.optimizer.calculate_wsjf_scores(features)
        
        # Step 3: Verify WSJF calculation accuracy
        # WSJF = (Business Value + Time Criticality + Risk Reduction) / Effort
        
        f001_wsjf = (9 + 8 + 7) / 5  # = 4.8
        f002_wsjf = (6 + 3 + 4) / 13  # = 1.0
        f003_wsjf = (10 + 9 + 8) / 3  # = 9.0
        
        scored_dict = {f.id: f.wsjf_score for f in scored_features}
        
        assert abs(scored_dict["F001"] - f001_wsjf) < 0.1
        assert abs(scored_dict["F002"] - f002_wsjf) < 0.1
        assert abs(scored_dict["F003"] - f003_wsjf) < 0.1
        
        # Step 4: Verify prioritization order
        sorted_features = sorted(scored_features, key=lambda f: f.wsjf_score, reverse=True)
        assert sorted_features[0].id == "F003"  # Highest WSJF
        assert sorted_features[1].id == "F001"  # Second highest
        assert sorted_features[2].id == "F002"  # Lowest WSJF

    def test_mvp_scope_optimization_with_constraints(self):
        """
        VERIFIES: MVP scope optimization under resource constraints
        SCENARIO: Optimize feature selection within budget and timeline limits
        """
        # Step 1: Define resource constraints
        constraints = ResourceConstraints(
            max_budget=50000,
            max_timeline_weeks=12,
            max_team_effort_hours=400,
            must_have_features=["F001", "F003"],  # Core requirements
            nice_to_have_features=["F002", "F004", "F005"],
            constraints_priority="budget"  # Budget is primary constraint
        )
        
        # Step 2: Create feature set exceeding constraints
        features = [
            Mock(id="F001", name="Core Tracking", estimated_cost=8000, estimated_hours=80, wsjf_score=8.5),
            Mock(id="F002", name="Smart Notifications", estimated_cost=12000, estimated_hours=120, wsjf_score=7.2),
            Mock(id="F003", name="User Registration", estimated_cost=6000, estimated_hours=60, wsjf_score=9.1),
            Mock(id="F004", name="Social Sharing", estimated_cost=15000, estimated_hours=150, wsjf_score=4.3),
            Mock(id="F005", name="Advanced Analytics", estimated_cost=25000, estimated_hours=200, wsjf_score=3.8),
            Mock(id="F006", name="Wearable Integration", estimated_cost=18000, estimated_hours=180, wsjf_score=5.2)
        ]
        
        # Step 3: Run MVP optimization
        mvp_result = self.optimizer.optimize_mvp_scope(features, constraints)
        
        # Step 4: Verify constraint compliance
        assert mvp_result.total_cost <= constraints.max_budget
        assert mvp_result.total_effort_hours <= constraints.max_team_effort_hours
        
        # Step 5: Verify must-have features included
        selected_ids = [f.id for f in mvp_result.selected_features]
        assert "F001" in selected_ids  # Must-have core tracking
        assert "F003" in selected_ids  # Must-have user registration
        
        # Step 6: Verify optimization logic (high WSJF features prioritized)
        deferred_ids = [f.id for f in mvp_result.deferred_features]
        
        # Lower WSJF features should be deferred when over budget
        if mvp_result.total_cost + 25000 > constraints.max_budget:
            assert "F005" in deferred_ids  # Expensive, low WSJF analytics

    def test_feasibility_analysis_and_risk_assessment(self):
        """
        VERIFIES: Feasibility analysis and risk assessment for MVP scope
        SCENARIO: Analyze technical and business feasibility of selected features
        """
        # Step 1: Create MVP scope with varying feasibility
        mvp_features = [
            Mock(
                id="F001",
                name="Basic Water Logging",
                technical_complexity=3,    # Low complexity
                market_risk=2,            # Low market risk
                integration_complexity=2,  # Low integration risk
                estimated_hours=40
            ),
            Mock(
                id="F002", 
                name="AI-Powered Recommendations",
                technical_complexity=9,    # Very high complexity
                market_risk=7,            # High market risk (unproven)
                integration_complexity=8,  # High integration complexity
                estimated_hours=300
            ),
            Mock(
                id="F003",
                name="User Profile Management", 
                technical_complexity=4,    # Medium complexity
                market_risk=1,            # Very low market risk
                integration_complexity=3,  # Low integration complexity
                estimated_hours=60
            )
        ]
        
        team_capability = Mock(
            experience_level=7,  # 1-10 scale
            ai_ml_experience=3,  # Limited AI/ML experience
            available_hours_per_week=80  # 2 developers × 40 hours
        )
        
        # Step 2: Run feasibility analysis
        feasibility_result = self.optimizer.analyze_mvp_feasibility(mvp_features, team_capability)
        
        # Step 3: Verify feasibility scoring
        assert feasibility_result.overall_feasibility_score <= 1.0
        
        feature_feasibility = {f.id: f.feasibility_score for f in feasibility_result.feature_analysis}
        
        # Basic logging should be highly feasible
        assert feature_feasibility["F001"] >= 0.8
        
        # AI recommendations should be low feasibility (complex + limited team experience)  
        assert feature_feasibility["F002"] <= 0.4
        
        # User management should be moderate feasibility
        assert 0.5 <= feature_feasibility["F003"] <= 0.8
        
        # Step 4: Verify risk recommendations
        high_risk_features = [f for f in feasibility_result.feature_analysis if f.feasibility_score < 0.5]
        assert len(high_risk_features) >= 1
        assert any(f.id == "F002" for f in high_risk_features)

    def test_resource_allocation_and_timeline_planning(self):
        """
        VERIFIES: Resource allocation and timeline planning for MVP
        SCENARIO: Allocate team resources and create realistic timeline
        """
        # Step 1: Define MVP scope
        mvp_features = [
            Mock(id="F001", name="User Auth", estimated_hours=80, dependencies=[]),
            Mock(id="F002", name="Water Logging", estimated_hours=60, dependencies=["F001"]),
            Mock(id="F003", name="Notifications", estimated_hours=100, dependencies=["F001", "F002"]),
            Mock(id="F004", name="Progress Dashboard", estimated_hours=120, dependencies=["F002"])
        ]
        
        # Step 2: Define team resources  
        team_resources = Mock(
            developers=[
                Mock(name="Dev A", skills=["Python", "React"], velocity=0.8, hours_per_week=40),
                Mock(name="Dev B", skills=["Python", "PostgreSQL"], velocity=0.9, hours_per_week=40)
            ],
            total_available_hours=960,  # 12 weeks × 80 hours/week
            sprint_length_weeks=2
        )
        
        # Step 3: Generate resource allocation plan
        allocation_result = self.optimizer.allocate_resources_and_timeline(mvp_features, team_resources)
        
        # Step 4: Verify resource allocation
        assert allocation_result.total_estimated_hours <= team_resources.total_available_hours
        assert len(allocation_result.sprint_plan) <= 6  # 12 weeks / 2 week sprints
        
        # Step 5: Verify dependency ordering
        sprint_plan = allocation_result.sprint_plan
        
        # F001 (User Auth) should be in early sprint (no dependencies)
        auth_sprint = next(s for s in sprint_plan if any(f.id == "F001" for f in s.features))
        
        # F003 (Notifications) should be after F001 and F002 (has dependencies)
        notif_sprint = next(s for s in sprint_plan if any(f.id == "F003" for f in s.features))
        
        assert auth_sprint.sprint_number < notif_sprint.sprint_number

    def test_mvp_cut_line_optimization(self):
        """
        VERIFIES: MVP cut-line optimization balancing value, risk, and cost
        SCENARIO: Find optimal feature cut-line maximizing value within constraints
        """
        # Step 1: Create feature value/cost/risk matrix
        features = [
            Mock(id="F001", name="Core Tracking", value=10, cost=5, risk=2, effort=40),     # High value, low cost
            Mock(id="F002", name="Basic Reminders", value=8, cost=3, risk=1, effort=30),   # Good value/cost
            Mock(id="F003", name="User Profiles", value=7, cost=4, risk=2, effort=50),     # Moderate all
            Mock(id="F004", name="Social Features", value=5, cost=8, risk=6, effort=120),  # Low value/cost
            Mock(id="F005", name="AI Insights", value=9, cost=12, risk=9, effort=200),     # High value, high risk
            Mock(id="F006", name="Wearable Sync", value=6, cost=7, risk=5, effort=90)      # Moderate value, cost
        ]
        
        # Step 2: Set optimization constraints
        optimization_constraints = {
            "max_cost": 25,
            "max_effort": 200,
            "max_risk_tolerance": 4,
            "min_total_value": 20
        }
        
        # Step 3: Find optimal cut-line
        cut_result = self.optimizer.find_optimal_mvp_cut_line(features, optimization_constraints)
        
        # Step 4: Verify optimization results
        assert cut_result.total_cost <= optimization_constraints["max_cost"]
        assert cut_result.total_effort <= optimization_constraints["max_effort"]
        assert cut_result.total_value >= optimization_constraints["min_total_value"]
        
        # Step 5: Verify high-value, low-cost features included
        selected_ids = [f.id for f in cut_result.selected_features]
        assert "F001" in selected_ids  # High value, low cost, low risk
        assert "F002" in selected_ids  # Good value/cost ratio
        
        # Step 6: Verify high-risk features appropriately handled
        deferred_ids = [f.id for f in cut_result.deferred_features]
        if cut_result.avg_risk > optimization_constraints["max_risk_tolerance"]:
            assert "F005" in deferred_ids  # High risk AI features deferred

    def test_value_density_optimization(self):
        """
        VERIFIES: Value density optimization for MVP feature selection
        SCENARIO: Maximize value per unit of cost and effort
        """
        # Step 1: Create features with different value densities
        features = [
            Mock(id="F001", name="Quick Win Feature", value=8, cost=2, effort=20),    # Value density: 4.0
            Mock(id="F002", name="Core Feature", value=10, cost=5, effort=60),        # Value density: 2.0
            Mock(id="F003", name="Expensive Feature", value=7, cost=15, effort=180), # Value density: 0.47
            Mock(id="F004", name="Low Value Feature", value=3, cost=8, effort=100)   # Value density: 0.375
        ]
        
        # Step 2: Calculate value density rankings
        density_rankings = self.optimizer.calculate_value_density_rankings(features)
        
        # Step 3: Verify ranking order (highest density first)
        assert density_rankings[0].id == "F001"  # Highest value density
        assert density_rankings[1].id == "F002"  # Second highest
        assert density_rankings[2].id == "F003"  # Third
        assert density_rankings[3].id == "F004"  # Lowest density
        
        # Step 4: Verify density calculations
        f001_density = density_rankings[0].value_density
        expected_f001_density = 8 / (2 + 20/40)  # value / (cost + effort_cost)
        assert abs(f001_density - expected_f001_density) < 0.1

    def test_risk_adjusted_mvp_planning(self):
        """
        VERIFIES: Risk-adjusted MVP planning and mitigation strategies  
        SCENARIO: Account for technical and market risks in MVP scope
        """
        # Step 1: Create features with different risk profiles
        features = [
            Mock(
                id="F001",
                name="Proven Technology Feature",
                value=8,
                technical_risk=2,     # Low technical risk
                market_risk=1,       # Low market risk
                integration_risk=2,  # Low integration risk
                effort=50
            ),
            Mock(
                id="F002",
                name="Experimental AI Feature", 
                value=9,
                technical_risk=9,     # Very high technical risk
                market_risk=7,       # High market risk (unproven demand)
                integration_risk=8,  # High integration complexity
                effort=180
            ),
            Mock(
                id="F003",
                name="Standard Web Feature",
                value=7,
                technical_risk=3,     # Low-medium technical risk
                market_risk=2,       # Low market risk
                integration_risk=4,  # Medium integration risk
                effort=80
            )
        ]
        
        # Step 2: Set risk tolerance levels
        risk_tolerance = Mock(
            technical_risk_max=6,      # Medium risk tolerance
            market_risk_max=5,         # Medium market risk tolerance  
            integration_risk_max=6,    # Medium integration risk tolerance
            overall_risk_budget=15     # Total risk budget across features
        )
        
        # Step 3: Run risk-adjusted optimization
        risk_result = self.optimizer.optimize_mvp_with_risk_adjustment(features, risk_tolerance)
        
        # Step 4: Verify risk compliance
        assert risk_result.total_technical_risk <= risk_tolerance.technical_risk_max * len(risk_result.selected_features)
        assert risk_result.total_risk_score <= risk_tolerance.overall_risk_budget
        
        # Step 5: Verify high-risk features appropriately handled
        selected_ids = [f.id for f in risk_result.selected_features]
        deferred_ids = [f.id for f in risk_result.deferred_features]
        
        # Low risk features should be selected
        assert "F001" in selected_ids  # Proven technology
        assert "F003" in selected_ids  # Standard web feature
        
        # Very high risk features should be deferred or have mitigation
        if "F002" in selected_ids:
            # If included, should have risk mitigation plan
            f002_feature = next(f for f in risk_result.selected_features if f.id == "F002")
            assert hasattr(f002_feature, 'risk_mitigation_plan')
            assert len(f002_feature.risk_mitigation_plan) > 0
        else:
            # If too risky, should be deferred
            assert "F002" in deferred_ids

    def test_resource_capacity_planning(self):
        """
        VERIFIES: Resource capacity planning and workload distribution
        SCENARIO: Plan developer workload and identify capacity constraints
        """
        # Step 1: Define team capacity
        team_capacity = [
            Mock(
                name="Senior Developer",
                skills=["Python", "React", "PostgreSQL", "AWS"],
                experience_years=5,
                hours_per_week=40,
                efficiency_factor=1.2  # 20% above average productivity
            ),
            Mock(
                name="Junior Developer",
                skills=["Python", "React"],
                experience_years=1,
                hours_per_week=40, 
                efficiency_factor=0.8  # 20% below average (learning curve)
            )
        ]
        
        # Step 2: Define feature requirements
        mvp_features = [
            Mock(
                id="F001",
                name="Backend API",
                required_skills=["Python", "PostgreSQL"],
                estimated_hours=120,
                complexity_level=7
            ),
            Mock(
                id="F002",
                name="Frontend Dashboard", 
                required_skills=["React", "TypeScript"],
                estimated_hours=100,
                complexity_level=5
            ),
            Mock(
                id="F003",
                name="DevOps Setup",
                required_skills=["AWS", "Docker"],
                estimated_hours=60,
                complexity_level=8
            )
        ]
        
        # Step 3: Plan resource allocation
        capacity_result = self.optimizer.plan_resource_capacity(mvp_features, team_capacity)
        
        # Step 4: Verify capacity planning
        assert capacity_result.total_available_hours > 0
        assert capacity_result.total_required_hours <= capacity_result.total_available_hours * 1.1  # 10% buffer
        
        # Step 5: Verify skill matching
        allocations = capacity_result.developer_allocations
        
        # Senior dev should get complex features requiring advanced skills
        senior_tasks = allocations["Senior Developer"]
        senior_feature_ids = [task.feature_id for task in senior_tasks]
        
        if "F003" in [f.id for f in mvp_features]:  # DevOps task
            assert "F003" in senior_feature_ids  # Requires AWS skills
        
        # Junior dev should get appropriate complexity features
        junior_tasks = allocations["Junior Developer"]
        junior_complexities = [task.complexity_level for task in junior_tasks]
        assert all(complexity <= 6 for complexity in junior_complexities)  # Not too complex

    def test_mvp_iteration_planning(self):
        """
        VERIFIES: MVP iteration and incremental delivery planning
        SCENARIO: Plan MVP in iterative releases with feedback loops
        """
        # Step 1: Define complete feature backlog
        complete_backlog = [
            Mock(id="F001", name="Core Tracking", value=10, effort=40, dependencies=[]),
            Mock(id="F002", name="User Auth", value=9, effort=60, dependencies=[]),
            Mock(id="F003", name="Notifications", value=8, effort=80, dependencies=["F001", "F002"]),
            Mock(id="F004", name="Analytics", value=7, effort=120, dependencies=["F001"]),
            Mock(id="F005", name="Social", value=5, effort=100, dependencies=["F002"])
        ]
        
        # Step 2: Plan iterative releases
        iteration_constraints = Mock(
            iteration_length_weeks=3,
            max_features_per_iteration=2,
            target_user_feedback_cycles=3,
            minimum_viable_iteration_value=15
        )
        
        iteration_plan = self.optimizer.plan_mvp_iterations(complete_backlog, iteration_constraints)
        
        # Step 3: Verify iteration planning
        assert len(iteration_plan.iterations) <= 4  # Reasonable number of iterations
        
        # Step 4: Verify dependency ordering within iterations
        for iteration in iteration_plan.iterations:
            for feature in iteration.features:
                # All dependencies should be in previous iterations
                for dep_id in feature.dependencies:
                    dep_found_in_previous = False
                    for prev_iter in iteration_plan.iterations:
                        if prev_iter.iteration_number >= iteration.iteration_number:
                            break
                        if any(f.id == dep_id for f in prev_iter.features):
                            dep_found_in_previous = True
                            break
                    
                    if feature.dependencies:  # Only check if has dependencies
                        assert dep_found_in_previous, f"Dependency {dep_id} not found in previous iterations"
        
        # Step 5: Verify minimum viable value per iteration
        for iteration in iteration_plan.iterations:
            iteration_value = sum(f.value for f in iteration.features)
            assert iteration_value >= iteration_constraints.minimum_viable_iteration_value

    def test_cost_estimation_and_budget_tracking(self):
        """
        VERIFIES: Cost estimation accuracy and budget tracking
        SCENARIO: Estimate MVP costs and track against budget constraints
        """
        # Step 1: Create detailed cost breakdown
        mvp_scope = [
            Mock(
                id="F001",
                name="Backend Development",
                development_hours=120,
                hourly_rate=75,
                infrastructure_cost_monthly=150,
                third_party_services_monthly=50
            ),
            Mock(
                id="F002", 
                name="Frontend Development",
                development_hours=100,
                hourly_rate=75,
                infrastructure_cost_monthly=0,  # Shares backend infrastructure
                third_party_services_monthly=25  # Analytics service
            ),
            Mock(
                id="F003",
                name="Testing & QA",
                development_hours=60,
                hourly_rate=65,  # QA rate
                infrastructure_cost_monthly=50,  # Test environment
                third_party_services_monthly=0
            )
        ]
        
        project_timeline_months = 3
        
        # Step 2: Calculate comprehensive cost estimation
        cost_estimation = self.optimizer.estimate_mvp_costs(mvp_scope, project_timeline_months)
        
        # Step 3: Verify cost calculation accuracy
        expected_dev_cost = (120 + 100) * 75 + 60 * 65  # Development costs
        expected_infra_cost = (150 + 50) * 3  # Infrastructure for 3 months
        expected_services_cost = (50 + 25) * 3  # Third-party services for 3 months
        
        assert abs(cost_estimation.development_cost - expected_dev_cost) < 100
        assert abs(cost_estimation.infrastructure_cost - expected_infra_cost) < 50
        assert abs(cost_estimation.services_cost - expected_services_cost) < 25
        
        # Step 4: Verify budget tracking
        budget_limit = 30000
        budget_status = self.optimizer.track_budget_compliance(cost_estimation, budget_limit)
        
        assert budget_status.total_estimated_cost == cost_estimation.total_cost
        assert budget_status.budget_utilization_percent <= 100.0
        
        if cost_estimation.total_cost > budget_limit:
            assert budget_status.over_budget == True
            assert len(budget_status.cost_reduction_recommendations) > 0

    def test_feature_dependency_graph_validation(self):
        """
        VERIFIES: Feature dependency graph validation and cycle detection
        SCENARIO: Validate feature dependencies don't create circular references
        """
        # Step 1: Create features with complex dependencies
        features_with_deps = [
            Mock(id="F001", name="User System", dependencies=[]),
            Mock(id="F002", name="Data Layer", dependencies=["F001"]),
            Mock(id="F003", name="API Layer", dependencies=["F001", "F002"]),
            Mock(id="F004", name="Frontend", dependencies=["F003"]),
            Mock(id="F005", name="Analytics", dependencies=["F002", "F003"])
        ]
        
        # Step 2: Test valid dependency graph
        valid_graph_result = self.optimizer.validate_feature_dependency_graph(features_with_deps)
        
        assert valid_graph_result.has_cycles == False
        assert valid_graph_result.is_valid == True
        assert len(valid_graph_result.topological_order) == 5
        
        # Verify topological ordering
        topo_order = [f.id for f in valid_graph_result.topological_order]
        assert topo_order.index("F001") < topo_order.index("F002")  # F001 before F002
        assert topo_order.index("F002") < topo_order.index("F003")  # F002 before F003
        
        # Step 3: Test circular dependency detection
        circular_features = features_with_deps.copy()
        circular_features[0].dependencies = ["F004"]  # Creates F001 → F002 → F003 → F004 → F001 cycle
        
        circular_result = self.optimizer.validate_feature_dependency_graph(circular_features)
        
        assert circular_result.has_cycles == True
        assert circular_result.is_valid == False
        assert len(circular_result.detected_cycles) >= 1

    def test_mvp_success_metrics_planning(self):
        """
        VERIFIES: MVP success metrics definition and tracking setup
        SCENARIO: Define measurable success criteria for MVP validation
        """
        # Step 1: Define MVP scope with business objectives
        mvp_scope = Mock(
            target_user_segment="Health-conscious professionals",
            core_value_proposition="Effortless hydration tracking",
            business_model="Freemium with premium analytics",
            timeline_weeks=12,
            budget=45000
        )
        
        # Step 2: Generate success metrics framework
        success_metrics = self.optimizer.define_mvp_success_metrics(mvp_scope)
        
        # Step 3: Verify metric categories
        assert "user_acquisition" in success_metrics
        assert "user_engagement" in success_metrics  
        assert "product_market_fit" in success_metrics
        assert "technical_performance" in success_metrics
        assert "business_viability" in success_metrics
        
        # Step 4: Verify metric measurability
        for category, metrics in success_metrics.items():
            for metric in metrics:
                assert metric.target_value is not None
                assert metric.measurement_method is not None
                assert metric.tracking_frequency is not None
        
        # Step 5: Verify metric specificity for MVP
        user_metrics = success_metrics["user_acquisition"]
        engagement_metrics = success_metrics["user_engagement"]
        
        # Should have specific, measurable targets
        assert any("MAU" in metric.name or "downloads" in metric.name for metric in user_metrics)
        assert any("retention" in metric.name or "session" in metric.name for metric in engagement_metrics)


class TestMVPOptimizerIntegration:
    """Test MVP optimizer integration with other pipeline components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.optimizer = MVPOptimizer()

    def test_paradigm_to_mvp_scope_integration(self):
        """
        VERIFIES: Integration between paradigm selection and MVP scoping
        SCENARIO: Paradigm framework influences MVP optimization strategy
        """
        # Step 1: YC paradigm should prioritize market validation speed
        yc_optimization = self.optimizer.get_paradigm_optimization_strategy("yc_startup")
        
        assert yc_optimization.prioritize_speed == True
        assert yc_optimization.market_validation_emphasis == "high"
        assert yc_optimization.feature_selection_bias == "market_tested"
        
        # Step 2: Lean Startup should prioritize learning and experimentation
        lean_optimization = self.optimizer.get_paradigm_optimization_strategy("lean_startup")
        
        assert lean_optimization.prioritize_learning == True
        assert lean_optimization.experiment_friendly_features == True
        assert lean_optimization.feature_selection_bias == "hypothesis_driven"
        
        # Step 3: Design Thinking should prioritize user experience
        dt_optimization = self.optimizer.get_paradigm_optimization_strategy("design_thinking")
        
        assert dt_optimization.prioritize_ux == True
        assert dt_optimization.user_testing_emphasis == "high"
        assert dt_optimization.feature_selection_bias == "user_centered"

    def test_mvp_to_code_generation_integration(self):
        """
        VERIFIES: MVP optimization results flow into code generation
        SCENARIO: MVP feature selection determines code generation scope
        """
        # Step 1: Create MVP optimization result
        mvp_result = Mock(
            selected_features=[
                Mock(id="F001", name="Water Logging", priority="must_have"),
                Mock(id="F002", name="Basic Reminders", priority="should_have")
            ],
            deferred_features=[
                Mock(id="F003", name="Social Sharing", priority="nice_to_have"),
                Mock(id="F004", name="Advanced Analytics", priority="future")
            ],
            implementation_order=["F001", "F002"]
        )
        
        # Step 2: Generate code generation instructions from MVP
        codegen_instructions = self.optimizer.generate_codegen_instructions_from_mvp(mvp_result)
        
        # Step 3: Verify code generation scope
        assert len(codegen_instructions.priority_features) == 2
        assert codegen_instructions.priority_features[0] == "F001"  # Water logging first
        
        # Step 4: Verify deferred features excluded from initial generation
        assert "F003" not in codegen_instructions.priority_features
        assert "F004" not in codegen_instructions.priority_features
        assert "F003" in codegen_instructions.future_features
        assert "F004" in codegen_instructions.future_features

    def test_mvp_metrics_to_runtime_telemetry_integration(self):
        """
        VERIFIES: MVP success metrics integration with runtime telemetry
        SCENARIO: MVP metrics definitions become runtime telemetry requirements
        """
        # Step 1: Define MVP success metrics
        mvp_metrics = {
            "user_engagement": [
                Mock(name="Daily Active Users", target_value=1000, measurement_frequency="daily"),
                Mock(name="Session Duration", target_value=300, measurement_frequency="realtime")  # 5 min avg
            ],
            "technical_performance": [
                Mock(name="API Response Time", target_value=200, measurement_frequency="realtime"),  # 200ms p95
                Mock(name="App Crash Rate", target_value=0.01, measurement_frequency="daily")  # <1% crash rate
            ]
        }
        
        # Step 2: Generate telemetry requirements
        telemetry_config = self.optimizer.generate_telemetry_config_from_mvp_metrics(mvp_metrics)
        
        # Step 3: Verify telemetry configuration
        assert "metrics" in telemetry_config
        assert "alerts" in telemetry_config
        assert "dashboards" in telemetry_config
        
        # Step 4: Verify metric mapping
        realtime_metrics = [m for m in telemetry_config["metrics"] if m.frequency == "realtime"]
        assert len(realtime_metrics) >= 2  # Session duration, API response time
        
        # Step 5: Verify alert thresholds
        alerts = telemetry_config["alerts"]
        assert any("response_time" in alert.name.lower() for alert in alerts)
        assert any("crash" in alert.name.lower() for alert in alerts)