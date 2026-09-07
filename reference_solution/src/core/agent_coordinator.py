"""Agent Coordinator - REFERENCE SOLUTION"""
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

        self.steps = {
            "customer_profile": self.customer_profile_agent.analyze,
            "credit_risk": self.credit_risk_agent.analyze,
            "compliance": self.compliance_agent.analyze,
            "lending_policy": self.lending_policy_agent.analyze,
            "recommendation": self.recommendation_agent.analyze,
        }

    def run_workflow(self, application_id: str) -> Dict[str, Any]:
        plan = self.planner.build_plan(application_id)
        results: Dict[str, Any] = {}

        for step in plan:
            agent_name = step["agent"]
            if agent_name not in self.steps:
                raise KeyError(f"No coordinator step registered for agent '{agent_name}'")
            step_callable = self.steps[agent_name]
            results[agent_name] = step_callable(application_id=application_id, context=results)

        return results
