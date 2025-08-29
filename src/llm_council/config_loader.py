"""Configuration loading utilities for LLM Council CLI.

Loads:
- quality_gates.yaml (global thresholds / triggers)
- project_config.yaml (selected template config copy)

Provides lightweight dataclasses / accessors used by the CLI orchestration.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

DEFAULT_QUALITY_GATES = "config/quality_gates.yaml"
DEFAULT_PROJECT_CONFIG = "project_config.yaml"


@dataclass
class QualityGates:
    raw: Dict[str, Any]

    @property
    def consensus_thresholds(self) -> Dict[str, Any]:
        return self.raw.get("consensus_thresholds", {})

    @property
    def human_review(self) -> Dict[str, Any]:
        return self.raw.get("human_review_config", {})

    @property
    def blocking_gates(self) -> Dict[str, Any]:
        return self.raw.get("blocking_severity_gates", {})

    @property
    def consensus_algorithm(self) -> Dict[str, Any]:
        return self.raw.get("consensus_algorithm", {})


@dataclass
class ProjectTemplate:
    path: Path
    raw: Dict[str, Any]

    @property
    def stages(self):
        return self.raw.get("project_info", {}).get("stages", [])

    def human_policy(self, stage: str) -> Dict[str, Any]:
        return self.raw.get("human_review_policy", {}).get(stage, {})


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_quality_gates(root: Path) -> QualityGates:
    q_path = root / DEFAULT_QUALITY_GATES
    return QualityGates(raw=_load_yaml(q_path))


def load_project_template(root: Path, explicit: Optional[Path] = None) -> ProjectTemplate:
    if explicit:
        p = explicit
    else:
        p = root / DEFAULT_PROJECT_CONFIG
    return ProjectTemplate(path=p, raw=_load_yaml(p))
