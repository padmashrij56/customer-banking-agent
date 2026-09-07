"""
Automated Testing (Activity 3.1).

A small, fixed pytest smoke suite validating the platform's workflow
behavior structurally (Scope Decision 5) - not a comprehensive test suite.
None of these tests call the real OpenAI API: they check plan/registry/
validation *shape*, not LLM-generated content, so they run without any
credentials configured.

TODO: Participants implement the body of the three tests marked TODO below.
The other two tests (import/registration boilerplate) are prefilled.
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
    """
    TODO (Activity 3.1): Construct a PlannerAgent(), call
    build_plan(SAMPLE_APPLICATION_ID), and assert:
      - the result has exactly 5 steps
      - the set of step["agent"] values equals EXPECTED_STEP_NAMES
      - every step's "application_id" equals SAMPLE_APPLICATION_ID
    """
    # TODO: build the plan and assert on its shape as described above.
    planner = PlannerAgent()
    plan = planner.build_plan(SAMPLE_APPLICATION_ID)
    assert len(plan) == 5
    assert {step["agent"] for step in plan} == EXPECTED_STEP_NAMES
    assert all(step["application_id"] == SAMPLE_APPLICATION_ID for step in plan)
    # raise NotImplementedError("test_planner_builds_expected_plan is not implemented yet - see tests/test_workflow.py")


def test_agent_coordinator_registers_all_steps():
    """
    TODO (Activity 3.1): Construct an AgentCoordinator() and assert that
    set(coordinator.steps.keys()) == EXPECTED_STEP_NAMES, and that every
    value in coordinator.steps is callable.
    """
    # TODO: construct the coordinator and assert on its steps registry.
    coordinator = AgentCoordinator()
    assert set(coordinator.steps.keys()) == EXPECTED_STEP_NAMES
    assert all(callable(step_fn) for step_fn in coordinator.steps.values())
    # raise NotImplementedError("test_agent_coordinator_registers_all_steps is not implemented yet - see tests/test_workflow.py")


def test_workflow_validator_flags_missing_sections():
    """
    TODO (Activity 3.1): Construct a WorkflowValidator().
      - Call validate({}) (an empty result) and assert it returns a non-None
        list of errors (every required section is missing).
      - Call validate() again with a well-formed fake result dict containing
        all 5 required sections as empty dicts (customer_profile={},
        credit_risk={}, compliance={}, lending_policy={}) plus
        recommendation={"decision": "Approve"}, and assert it returns None.
    """
    # TODO: exercise WorkflowValidator.validate() with both an invalid and a
    # valid result shape, asserting the return values described above.
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
    # raise NotImplementedError("test_workflow_validator_flags_missing_sections is not implemented yet - see tests/test_workflow.py")
