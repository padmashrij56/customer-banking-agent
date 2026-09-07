"""Planner Agent - REFERENCE SOLUTION"""
from typing import Any, Dict, List

from src.services.loan_application_service import get_loan_application
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PlannerAgent:
    """Builds the fixed, linear execution plan across the five specialist
    agents for a loan application."""

    def __init__(self):
        config = load_yaml_config("config/agent_config.yaml")
        self.sequence: List[str] = config.get("planner", {}).get("sequence", [])

    def build_plan(self, application_id: str) -> List[Dict[str, Any]]:
        application = get_loan_application(application_id)
        if "error" in application:
            raise ValueError(application["error"])

        return [
            {"step": i + 1, "agent": name, "application_id": application_id}
            for i, name in enumerate(self.sequence)
        ]
