"""
Agent Coordinator.

TODO: Participants will implement run_workflow() (Activity 1.3) - this is
the "wire the 5 provided specialist agents into steps the Planner can
invoke" layer, distinct from writing any agent's internal logic (all 5
specialist agents are provided, complete, vendored-style - see Scope
Decision 1 in the Project Configuration).
"""
from typing import Any, Dict, Optional

from src.agents.compliance_agent import ComplianceAgent
from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.customer_profile_agent import CustomerProfileAgent
from src.agents.lending_policy_agent import LendingPolicyAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AgentCoordinator:
    """Wires the five specialist agents into named steps, then executes a
    Planner-built plan against them, aggregating each step's output into one
    combined workflow result."""

    def __init__(
        self,
        planner: Optional[PlannerAgent] = None,
        customer_profile_agent: Optional[CustomerProfileAgent] = None,
        credit_risk_agent: Optional[CreditRiskAgent] = None,
        compliance_agent: Optional[ComplianceAgent] = None,
        lending_policy_agent: Optional[LendingPolicyAgent] = None,
        recommendation_agent: Optional[RecommendationAgent] = None,
    ):
        self.planner = planner or PlannerAgent()
        self.customer_profile_agent = customer_profile_agent or CustomerProfileAgent()
        self.credit_risk_agent = credit_risk_agent or CreditRiskAgent()
        self.compliance_agent = compliance_agent or ComplianceAgent()
        self.lending_policy_agent = lending_policy_agent or LendingPolicyAgent()
        self.recommendation_agent = recommendation_agent or RecommendationAgent()

        # Prefilled wiring: step name -> the bound agent method that
        # executes it. These names must match what PlannerAgent.build_plan()
        # produces (config/agent_config.yaml's planner.sequence).
        self.steps = {
            "customer_profile": self.customer_profile_agent.analyze,
            "credit_risk": self.credit_risk_agent.analyze,
            "compliance": self.compliance_agent.analyze,
            "lending_policy": self.lending_policy_agent.analyze,
            "recommendation": self.recommendation_agent.analyze,
        }

    def run_workflow(self, application_id: str) -> Dict[str, Any]:
        """
        Execute the full workflow for `application_id` and return one
        aggregated result dict.

        TODO (Activity 1.3):
        1. Call self.planner.build_plan(application_id) to get the ordered
           list of step dicts (each has "agent" and "application_id" keys).
        2. Create an empty `results: Dict[str, Any] = {}` accumulator.
        3. For each step in the plan, in order:
           a. Look up the callable in self.steps by step["agent"]. If the
              name isn't registered, raise a KeyError naming the missing step.
           b. Call it as `callable(application_id=application_id, context=results)`
              - passing the results accumulated so far as `context`, so later
              steps (especially "recommendation") can read earlier steps'
              output.
           c. Store the returned dict under `results[step["agent"]] = <returned dict>`.
        4. Return `results` (a dict keyed by agent name: "customer_profile",
           "credit_risk", "compliance", "lending_policy", "recommendation" -
           this is the shape src/core/workflow_validator.py checks in
           Activity 2.3).
        """
        # TODO: build the plan, execute each step via self.steps, accumulate
        # results, and return the aggregated dict described above.
        plan = self.planner.build_plan(application_id)
        results: Dict[str, Any] = {}

        for step in plan:
            agent_name = step["agent"]
            if agent_name not in self.steps:
                raise KeyError(f"No coordinator step registered for agent '{agent_name}'")
            step_callable = self.steps[agent_name]
            results[agent_name] = step_callable(application_id=application_id, context=results)

        return results
        # raise NotImplementedError("AgentCoordinator.run_workflow is not implemented yet - see src/core/agent_coordinator.py")
