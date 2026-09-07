"""
Workflow Validator.

TODO: Participants will implement validate() (Activity 2.3) - structural,
in-workflow validation of an AgentCoordinator.run_workflow() result, before
it is treated as a finished recommendation. Not a comprehensive test suite -
that's tests/test_workflow.py (Activity 3.1); this is the platform checking
its own output shape at runtime.
"""
from typing import Any, Dict, List, Optional

from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class WorkflowValidator:
    """Validates the shape of an aggregated workflow result before it is
    returned to a caller (e.g. the Streamlit portal)."""

    def __init__(self):
        config = load_yaml_config("config/agent_config.yaml")
        self.rules = config.get("validation", {})

    def validate(self, result: Dict[str, Any]) -> Optional[List[str]]:
        """
        Check `result` (the dict AgentCoordinator.run_workflow() returns)
        against the expected shape. Return a list of human-readable error
        strings if anything is wrong, or None if `result` is valid.

        TODO (Activity 2.3):
        1. required_fields = self.rules.get("required_result_fields", []) -
           for each name in required_fields, check result has a key with
           that name and it's a dict (not missing, not None, not the wrong
           type). Collect a descriptive error string for each problem, e.g.
           f"Missing or invalid '{name}' section".
        2. Check that result.get("recommendation", {}).get("decision") is
           one of self.rules.get("allowed_decisions", []) - if not, append
           an error string naming the actual value found.
        3. Return the list of errors if non-empty, otherwise return None.
        """
        # TODO: check required sections are present, then check the final
        # decision value is one of the allowed decisions.
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
        # raise NotImplementedError("WorkflowValidator.validate is not implemented yet - see src/core/workflow_validator.py")
