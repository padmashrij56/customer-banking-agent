"""
Reference-solution verification harness (Part B of "Validation Before
Shipping" - see BootCamp_AI_DevelopmentSpecification.docx §6 and the
bootcamp-lab-builder skill's scripts/validate_workbook.py template).

Confirms the reference solution's logic is actually correct (not just
"doesn't crash"), with the paid OpenAI API mocked out. Since
reference_solution/src/ deliberately does NOT duplicate the
provided-complete modules (5 specialist agents, src/llm, src/utils,
src/knowledge - see the spec's "don't duplicate shared assets" rule), this
script builds a throwaway merged copy of the project (real src/ + provided
modules, with reference_solution's TODO modules overlaid on top) in a temp
directory, then:

  A. Overlays reference_solution/tests/test_workflow.py (the completed
     version of the shipped starter's three TODO tests) onto the merged
     copy and runs it via pytest - confirms the pytest suite in
     tests/test_workflow.py would pass once a participant's src/
     implementation matches the reference's.
  B. Exercises the full pipeline in-process with OpenAI mocked, asserting
     on actual returned values (plan shape, aggregated result shape,
     decision parsing, validator behavior).
  C. Exercises a REAL MCP client/server round-trip over a live stdio
     subprocess (launched from the merged temp copy), with no mocking -
     this is local IPC, not a paid call, so it runs for real.

Run: python scripts/verify_reference.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Files the starter ships as TODO stubs and reference_solution/ completes.
# build_merged_copy() overlays reference_solution/<rel> onto the copied
# project at <rel> for each of these.
TODO_MODULE_FILES = [
    Path("src/services/loan_application_service.py"),
    Path("src/services/credit_score_service.py"),
    Path("src/agents/planner_agent.py"),
    Path("src/core/agent_coordinator.py"),
    Path("src/core/workflow_validator.py"),
    Path("src/mcp/mcp_server.py"),
    Path("src/mcp/mcp_client.py"),
    Path("src/observability/tracing.py"),
    Path("tests/test_workflow.py"),
]

_IGNORE = shutil.ignore_patterns(
    ".git", "__pycache__", "*.pyc", ".ipynb_checkpoints", "reference_solution",
    "executed.ipynb", ".env", "cell_outputs.txt", "node_modules",
)


def build_merged_copy(tmp_dir: Path) -> Path:
    """Copy the real project into tmp_dir, then overlay each
    reference_solution/ TODO file (src modules + the solved test suite) on
    top of the copy."""
    target = tmp_dir / "project"
    shutil.copytree(PROJECT_ROOT, target, ignore=_IGNORE)

    for rel in TODO_MODULE_FILES:
        shutil.copyfile(PROJECT_ROOT / "reference_solution" / rel, target / rel)

    return target


def run_pytest_against_merged_copy(merged_root: Path) -> None:
    print("\n=== A. pytest tests/test_workflow.py against the merged (reference) copy ===")
    env = dict(os.environ)
    env["OPENAI_API_KEY"] = "sk-fake-key-for-mocked-verification"
    env["PYTHONPATH"] = str(merged_root)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_workflow.py", "-v"],
        cwd=str(merged_root), env=env, capture_output=True, text=True,
    )
    print(proc.stdout[-3000:])
    if proc.returncode != 0:
        print(proc.stderr[-2000:])
        raise AssertionError(f"pytest against the merged reference copy failed (exit {proc.returncode})")
    print("PASSED - pytest suite passes against the reference implementation.")


class FakeChoice:
    def __init__(self, content):
        self.message = MagicMock()
        self.message.content = content


class FakeCompletions:
    def create(self, model, messages, temperature, max_tokens):
        system = messages[0]["content"] if messages else ""
        if "Recommendation Agent" in system:
            return MagicMock(choices=[FakeChoice("Decision: Approve\nStrong applicant across all checks.")])
        return MagicMock(choices=[FakeChoice("Mocked LLM narrative for verification purposes.")])


class FakeEmbeddingItem:
    def __init__(self, vec):
        self.embedding = vec


class FakeEmbeddings:
    def create(self, model, input):
        texts = input if isinstance(input, list) else [input]
        return MagicMock(data=[FakeEmbeddingItem([0.001] * 1536) for _ in texts])


class FakeOpenAIClient:
    def __init__(self, *a, **kw):
        self.chat = MagicMock()
        self.chat.completions = FakeCompletions()
        self.embeddings = FakeEmbeddings()


def run_pipeline_checks(merged_root: Path) -> None:
    print("\n=== B. In-process pipeline checks (OpenAI mocked) ===")
    sys.path.insert(0, str(merged_root))
    os.environ["OPENAI_API_KEY"] = "sk-fake-key-for-mocked-verification"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"

    with patch("openai.OpenAI", FakeOpenAIClient):
        for name in list(sys.modules):
            if name == "src" or name.startswith("src."):
                del sys.modules[name]

        from src.agents.planner_agent import PlannerAgent
        from src.core.agent_coordinator import AgentCoordinator
        from src.core.workflow_validator import WorkflowValidator
        from src.observability.tracing import run_planner_with_tracing

        planner = PlannerAgent()
        plan = planner.build_plan("LOAN-5001")
        expected_order = ["customer_profile", "credit_risk", "compliance", "lending_policy", "recommendation"]
        assert [s["agent"] for s in plan] == expected_order, plan
        print("  [1] build_plan produces the expected 5-step ordered plan - OK")

        try:
            planner.build_plan("LOAN-9999")
            raise AssertionError("expected ValueError for an unknown application")
        except ValueError:
            print("  [2] build_plan raises ValueError for an unknown application - OK")

        coordinator = AgentCoordinator(planner=planner)
        assert set(coordinator.steps.keys()) == set(expected_order)
        print("  [3] AgentCoordinator registers all 5 steps - OK")

        result = coordinator.run_workflow("LOAN-5001")
        for key in expected_order:
            assert key in result and isinstance(result[key], dict), key
        assert result["recommendation"]["decision"] in ("Approve", "Refer", "Decline")
        print(f"  [4] run_workflow aggregates all 5 sections, decision={result['recommendation']['decision']!r} - OK")

        validator = WorkflowValidator()
        assert validator.validate(result) is None
        broken_errors = validator.validate({"customer_profile": {}, "recommendation": {"decision": "Maybe"}})
        assert broken_errors, "expected errors for a broken result"
        print("  [5] WorkflowValidator distinguishes a valid result from a broken one - OK")

        traced_result = run_planner_with_tracing(coordinator.run_workflow, "LOAN-5002")
        assert traced_result["recommendation"]["decision"] in ("Approve", "Refer", "Decline")
        print("  [6] run_planner_with_tracing runs correctly untraced (no LangSmith creds) - OK")

    sys.path.remove(str(merged_root))
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]


def run_mcp_roundtrip_check(merged_root: Path) -> None:
    print("\n=== C. Real MCP client/server round-trip (live stdio subprocess, no mocking) ===")
    sys.path.insert(0, str(merged_root))
    for name in list(sys.modules):
        if name == "src" or name.startswith("src."):
            del sys.modules[name]

    cwd = Path.cwd()
    os.chdir(merged_root)
    try:
        from src.mcp.mcp_client import fetch_credit_score_via_mcp
        result = fetch_credit_score_via_mcp("CUST-1002")
        assert result["credit_score"] == 701, result
        print("  fetched via a real MCP stdio round-trip:", result)
    finally:
        os.chdir(cwd)
        sys.path.remove(str(merged_root))
        for name in list(sys.modules):
            if name == "src" or name.startswith("src."):
                del sys.modules[name]


def main():
    with tempfile.TemporaryDirectory(prefix="bc3_verify_") as tmp:
        merged_root = build_merged_copy(Path(tmp))
        print(f"Built merged verification copy at {merged_root}")

        run_pytest_against_merged_copy(merged_root)
        run_pipeline_checks(merged_root)
        run_mcp_roundtrip_check(merged_root)

    print("\nAll reference-solution verification checks passed.")


if __name__ == "__main__":
    main()
