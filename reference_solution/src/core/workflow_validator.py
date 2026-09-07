"""Workflow Validator - REFERENCE SOLUTION"""
from typing import Any, Dict, List, Optional

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowValidator:
    """Validates the shape of an aggregated workflow result before it is
    returned to a caller."""

    def __init__(self):
        config = load_yaml_config("config/agent_config.yaml")
        self.rules = config.get("validation", {})

    def validate(self, result: Dict[str, Any]) -> Optional[List[str]]:
        errors: List[str] = []
        required_fields = self.rules.get("required_result_fields", [])

        for name in required_fields:
            section = result.get(name)
            if not isinstance(section, dict):
                errors.append(f"Missing or invalid '{name}' section")

        decision = (result.get("recommendation") or {}).get("decision")
        allowed_decisions = self.rules.get("allowed_decisions", [])
        if decision not in allowed_decisions:
            errors.append(f"Recommendation decision '{decision}' is not one of the allowed decisions {allowed_decisions}")

        return errors if errors else None
