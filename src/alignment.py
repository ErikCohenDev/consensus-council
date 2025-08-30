"""Document alignment validation system."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class DocumentDependency:
    """Represents a dependency relationship between document stages."""
    source_stage: str
    target_stage: str
    relationship: str


@dataclass
class AlignmentResult:
    """Result of alignment validation between two documents."""
    source_stage: str
    target_stage: str
    alignment_score: float
    is_aligned: bool
    misalignments: List[str]
    suggestions: List[str]


class AlignmentValidator:
    """Validates alignment between documents in the audit workflow."""

    def __init__(self):
        """Initialize validator with document dependency definitions."""
        self._dependencies = [
            DocumentDependency("research_brief", "market_scan", "informs"),
            DocumentDependency("market_scan", "vision", "validates_market_for"),
            DocumentDependency("vision", "prd", "defines_requirements_for"),
            DocumentDependency("prd", "architecture", "specifies_implementation_for"),
            DocumentDependency("architecture", "implementation_plan", "guides_tasks_for")
        ]

    def get_document_dependencies(self, target_stage: str) -> List[DocumentDependency]:
        """Get all dependencies for a target document stage."""
        return [dep for dep in self._dependencies if dep.target_stage == target_stage]

    def validate_alignment(self, source_stage: str, target_stage: str,
                          source_content: str, target_content: str) -> AlignmentResult:
        """Validate alignment between source and target documents."""
        misalignments = []
        suggestions = []

        # Handle missing documents
        if not source_content.strip():
            misalignments.append(f"Source document {source_stage} is missing or empty")
            suggestions.append(f"Create {source_stage} document before proceeding")
            return AlignmentResult(
                source_stage=source_stage,
                target_stage=target_stage,
                alignment_score=1.0,
                is_aligned=False,
                misalignments=misalignments,
                suggestions=suggestions
            )

        if not target_content.strip():
            misalignments.append(f"Target document {target_stage} is missing or empty")
            suggestions.append(f"Create {target_stage} document")
            return AlignmentResult(
                source_stage=source_stage,
                target_stage=target_stage,
                alignment_score=1.0,
                is_aligned=False,
                misalignments=misalignments,
                suggestions=suggestions
            )

        # Validate specific dependency relationships
        if source_stage == "vision" and target_stage == "prd":
            misalignments.extend(self._validate_vision_to_prd(source_content, target_content))
        elif source_stage == "prd" and target_stage == "architecture":
            misalignments.extend(self._validate_prd_to_architecture(source_content, target_content))
        elif source_stage == "architecture" and target_stage == "implementation_plan":
            misalignments.extend(self._validate_architecture_to_implementation(source_content, target_content))
        elif source_stage == "market_scan" and target_stage == "vision":
            misalignments.extend(self._validate_market_scan_to_vision(source_content, target_content))

        # Generate suggestions based on misalignments
        suggestions = self._generate_suggestions(misalignments, source_stage, target_stage)

        # Calculate alignment score based on misalignments
        alignment_score = max(1.0, 5.0 - (len(misalignments) * 1.2))
        is_aligned = alignment_score >= 3.5 and len(misalignments) <= 1

        return AlignmentResult(
            source_stage=source_stage,
            target_stage=target_stage,
            alignment_score=alignment_score,
            is_aligned=is_aligned,
            misalignments=misalignments,
            suggestions=suggestions
        )

    def _validate_vision_to_prd(self, vision_content: str, prd_content: str) -> List[str]:
        """Validate alignment from Vision to PRD."""
        misalignments = []

        # Check interface consistency
        vision_mentions_cli = "cli" in vision_content.lower()
        vision_mentions_web = "web" in vision_content.lower() and "interface" in vision_content.lower()
        prd_mentions_cli = "cli" in prd_content.lower()
        prd_mentions_web = "web" in prd_content.lower() and ("interface" in prd_content.lower() or "dashboard" in prd_content.lower())

        if vision_mentions_cli and prd_mentions_web and not prd_mentions_cli:
            misalignments.append("Vision focuses on CLI but PRD specifies web interface without CLI mention")

        if vision_mentions_web and prd_mentions_cli and not prd_mentions_web:
            misalignments.append("Vision mentions web interface but PRD only specifies CLI")

        # Check cost constraints
        vision_cost_pattern = r'\$(\d+(?:\.\d+)?)'
        vision_costs = re.findall(vision_cost_pattern, vision_content)
        prd_costs = re.findall(vision_cost_pattern, prd_content)

        if vision_costs and not prd_costs:
            misalignments.append(f"Vision specifies cost constraint ${vision_costs[0]} but PRD has no cost requirements")

        # Check target users
        vision_users = self._extract_users(vision_content)
        prd_users = self._extract_users(prd_content)

        if vision_users and prd_users:
            missing_users = vision_users - prd_users
            if missing_users:
                misalignments.append(f"Vision targets {', '.join(missing_users)} but PRD doesn't address these users")

        return misalignments

    def _validate_prd_to_architecture(self, prd_content: str, arch_content: str) -> List[str]:
        """Validate alignment from PRD to Architecture."""
        misalignments = []

        # Check that architecture addresses PRD requirements
        prd_requirements = re.findall(r'R-[A-Z0-9-]+:?\s*([^\n]+)', prd_content, re.IGNORECASE)

        for req in prd_requirements[:3]:  # Check first 3 requirements
            req_lower = req.lower()
            if "cli" in req_lower and "cli" not in arch_content.lower():
                misalignments.append(f"PRD requirement '{req}' not addressed in architecture")
            elif "web" in req_lower and "web" not in arch_content.lower():
                misalignments.append(f"PRD web requirement '{req}' not addressed in architecture")

        # Check performance requirements
        if "performance" in prd_content.lower() and "performance" not in arch_content.lower():
            misalignments.append("PRD mentions performance requirements but architecture lacks performance considerations")

        return misalignments

    def _validate_architecture_to_implementation(self, arch_content: str, impl_content: str) -> List[str]:
        """Validate alignment from Architecture to Implementation Plan."""
        misalignments = []

        # Check that implementation tasks map to architectural components
        arch_components = re.findall(r'(?:class|component|module|service)\s+(\w+)', arch_content, re.IGNORECASE)
        impl_tasks = re.findall(r'T-[0-9-]+:?\s*([^\n]+)', impl_content, re.IGNORECASE)

        if arch_components and impl_tasks:
            mentioned_components = []
            for component in arch_components[:3]:  # Check first 3 components
                for task in impl_tasks:
                    if component.lower() in task.lower():
                        mentioned_components.append(component)
                        break

            missing_components = set(arch_components[:3]) - set(mentioned_components)
            for component in missing_components:
                misalignments.append(f"Architecture component '{component}' has no corresponding implementation tasks")

        return misalignments

    def _validate_market_scan_to_vision(self, market_content: str, vision_content: str) -> List[str]:
        """Validate alignment from Market Scan to Vision."""
        misalignments = []

        # Check that vision addresses market findings
        if "competitor" in market_content.lower() and "competitor" not in vision_content.lower():
            misalignments.append("Market scan identifies competitors but vision doesn't address competitive differentiation")

        if "market size" in market_content.lower() and "market" not in vision_content.lower():
            misalignments.append("Market scan discusses market size but vision lacks market context")

        return misalignments

    def _extract_users(self, content: str) -> set[str]:
        """Extract user types mentioned in content."""
        user_patterns = [
            r'(?:target|for)\s+(\w+)s?\b',
            r'(\w+)s?\s+(?:need|want|use)',
            r'(?:user|customer|audience):\s*(\w+)'
        ]

        users = set()
        content_lower = content.lower()

        for pattern in user_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            users.update(matches)

        # Filter to common user types
        user_types = {"founder", "pm", "engineer", "developer", "stakeholder", "manager"}
        return users & user_types

    def _generate_suggestions(self, misalignments: List[str], source_stage: str, target_stage: str) -> List[str]:
        """Generate suggestions to fix alignment issues."""
        if not misalignments:
            return [f"Good alignment between {source_stage} and {target_stage}"]

        suggestions = []

        for misalignment in misalignments:
            if "interface" in misalignment.lower():
                suggestions.append("Align interface specifications between documents")
            elif "cost" in misalignment.lower():
                suggestions.append("Add cost constraints to ensure consistency")
            elif "user" in misalignment.lower():
                suggestions.append("Ensure target users are consistent across documents")
            elif "component" in misalignment.lower():
                suggestions.append("Add implementation tasks for all architectural components")
            elif "missing" in misalignment.lower():
                suggestions.append("Create missing document before proceeding")
            else:
                suggestions.append(f"Review and align {source_stage} and {target_stage} content")

        return suggestions[:5]  # Limit to top 5 suggestions

    def validate_document_chain(self, documents: Dict[str, str]) -> List[AlignmentResult]:
        """Validate alignment across entire document chain."""
        results = []

        for dependency in self._dependencies:
            source_content = documents.get(dependency.source_stage, "")
            target_content = documents.get(dependency.target_stage, "")

            result = self.validate_alignment(
                dependency.source_stage,
                dependency.target_stage,
                source_content,
                target_content
            )
            results.append(result)

        return results

    def generate_backlog_file(self, alignment_result: AlignmentResult) -> str:
        """Generate alignment backlog markdown file content."""
        lines = []
        lines.append(f"# ALIGNMENT BACKLOG: {alignment_result.source_stage.upper()} → {alignment_result.target_stage.upper()}")
        lines.append("")
        lines.append(f"**Alignment Score:** {alignment_result.alignment_score:.1f}/5.0")
        lines.append(f"**Status:** {'✅ ALIGNED' if alignment_result.is_aligned else '❌ MISALIGNED'}")
        lines.append("")

        if alignment_result.misalignments:
            lines.append("## 🚨 Detected Misalignments")
            lines.append("")
            for i, misalignment in enumerate(alignment_result.misalignments, 1):
                lines.append(f"{i}. {misalignment}")
            lines.append("")

        if alignment_result.suggestions:
            lines.append("## 💡 Suggested Fixes")
            lines.append("")
            for i, suggestion in enumerate(alignment_result.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        lines.append("## 📝 Next Steps")
        lines.append("")
        if alignment_result.is_aligned:
            lines.append("- Document alignment is acceptable, proceed with next stage")
        else:
            lines.append("- Address misalignments before proceeding")
            lines.append("- Re-run alignment validation after fixes")

        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by LLM Council Alignment Validator*")

        return "\n".join(lines)


__all__ = ["AlignmentValidator", "AlignmentResult", "DocumentDependency"]
