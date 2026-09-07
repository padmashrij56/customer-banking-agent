"""Automated Testing (Activity 3.1) - REFERENCE SOLUTION.

The completed version of the shipped starter `tests/test_workflow.py`:
same imports, constants, and two prefilled tests, with the three TODO
tests implemented. A small, fixed structural smoke suite - none of these
tests call the real OpenAI API, so they run without any credentials.
"""
from src.agents.compliance_agent import ComplianceAgent
from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.customer_profile_agent import CustomerProfileAgent
from src.agents.lending_policy_agent import LendingPolicyAgent
from src.agents.planner_agent import PlannerAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.core.agent_coordinator import AgentCoordinator
from src.core.workflow_validator import WorkflowValidator
from src.mcp import mcp_server

SAMPLE_APPLICATION_ID = "LOAN-5001"
EXPECTED_STEP_NAMES = {"customer_profile", "credit_risk", "compliance", "lending_policy", "recommendation"}


def test_specialist_agents_are_importable():
    """Prefilled - structural check that all 5 specialist agents expose the
    common analyze() interface the coordinator relies on."""
    for agent_cls in (
        CustomerProfileAgent,
        CreditRiskAgent,
        ComplianceAgent,
        LendingPolicyAgent,
        RecommendationAgent,
    ):
        assert hasattr(agent_cls, "analyze"), f"{agent_cls.__name__} is missing an analyze() method"


def test_mcp_server_tool_registered():
    """Prefilled - structural check that the MCP server module defines the
    one wrapped tool function (Activity 2.1), without starting the server
    or making any network call."""
    assert hasattr(mcp_server, "get_credit_score_tool")
    assert hasattr(mcp_server, "mcp_app")


def test_planner_builds_expected_plan():
    """Activity 3.1: the plan has exactly 5 steps, its agent names match
    EXPECTED_STEP_NAMES, and every step carries the requested id."""
    planner = PlannerAgent()
    plan = planner.build_plan(SAMPLE_APPLICATION_ID)
    assert len(plan) == 5
    assert {step["agent"] for step in plan} == EXPECTED_STEP_NAMES
    assert all(step["application_id"] == SAMPLE_APPLICATION_ID for step in plan)


def test_agent_coordinator_registers_all_steps():
    """Activity 3.1: the coordinator's step registry has exactly the 5
    expected names, each mapped to a callable."""
    coordinator = AgentCoordinator()
    assert set(coordinator.steps.keys()) == EXPECTED_STEP_NAMES
    assert all(callable(step_fn) for step_fn in coordinator.steps.values())


def test_workflow_validator_flags_missing_sections():
    """Activity 3.1: an empty result yields a non-empty error list; a
    well-formed result with all 5 sections and an allowed decision yields
    None."""
    validator = WorkflowValidator()

    errors = validator.validate({})
    assert errors is not None and len(errors) > 0

    well_formed = {
        "customer_profile": {},
        "credit_risk": {},
        "compliance": {},
        "lending_policy": {},
        "recommendation": {"decision": "Approve"},
    }
    assert validator.validate(well_formed) is None
