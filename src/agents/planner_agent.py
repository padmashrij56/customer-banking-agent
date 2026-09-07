"""
Planner Agent.

TODO: Participants will implement build_plan() (Activity 1.2), together
with the two loan-domain service lookups it depends on
(src/services/loan_application_service.py, src/services/credit_score_service.py -
same activity, see the workbook's Activity 1.2 instructions).
"""
from typing import Any, Dict, List, Optional
from src.services.loan_application_service import get_loan_application
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class PlannerAgent:
    """Builds the fixed, linear execution plan across the five specialist
    agents for a loan application (Scope Decision 6 - a single illustrative
    orchestration pattern, not a dynamic/branching planner that reasons
    about which agents to skip or reorders based on intermediate results).

    The actual execution of the plan (invoking each agent, aggregating
    results) is src/core/agent_coordinator.py's job (Activity 1.3) - this
    class only decides *what* to run and in what order.
    """

    def __init__(self):
        config = load_yaml_config("config/agent_config.yaml")
        self.sequence: List[str] = config.get("planner", {}).get("sequence", [])

    def build_plan(self, application_id: str) -> List[Dict[str, Any]]:
        """
        Build the ordered list of steps for `application_id`.

        TODO (Activity 1.2):
        1. Call get_loan_application(application_id). If the result contains
           an "error" key, raise a ValueError with that error message - the
           plan can't be built for an application that doesn't exist.
        2. Otherwise, build and return a list of step dicts, one per name in
           self.sequence (which is the fixed order loaded from
           config/agent_config.yaml's planner.sequence - Customer Profile,
           Credit Risk, Compliance, Lending Policy, Recommendation), each
           shaped like:
               {"step": <1-based index>, "agent": <step name>, "application_id": application_id}
           The "agent" value must match the step names
           src/core/agent_coordinator.py registers in Activity 1.3, so don't
           rename them - use self.sequence values as-is.
        """
        # TODO: validate the application exists, then build the ordered
        # list of step dicts described above.
        application = get_loan_application(application_id)
        if "error" in application:
            raise ValueError(application["error"])

        return [
            {"step": i + 1, "agent": name, "application_id": application_id}
            for i, name in enumerate(self.sequence)
        ]
        # raise NotImplementedError("PlannerAgent.build_plan is not implemented yet - see src/agents/planner_agent.py")
