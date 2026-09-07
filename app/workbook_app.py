"""
Guided Project Workbook: interactive Streamlit runner.

The single entry point for the lab (Bootcamp 1/2 pattern - no notebook). Edit
the actual src/ files in your own IDE, then run each activity's validation
against them via a fresh subprocess (so results always reflect exactly
what's saved on disk, with no stale-import/kernel-state surprises). Every
script below is self-contained per activity (it rebuilds any earlier-activity
object it needs), so activities can be run in any order.
"""
import ast
import os
import subprocess
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
# override=True: load_dotenv() otherwise refuses to replace an env var that's
# already set in the shell, so a stray OPENAI_API_KEY left over from some
# other project (or a global shell profile export) would silently shadow
# this project's own .env with no error, just a confusing wrong-key failure.
load_dotenv(PROJECT_ROOT / ".env", override=True)

st.set_page_config(
    page_title="Guided Project Workbook",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Streamlit's floating top toolbar (Deploy button, hamburger menu) is
       position:absolute with a very high z-index, so it renders on top of
       page content rather than pushing it down. 4.5rem clears it with room
       to spare across the Streamlit versions this project has run on. */
    .block-container {padding-top: 4.5rem;}
    .hero-banner {
        background: linear-gradient(120deg, #0b2545 0%, #13315c 35%, #1f6f78 70%, #13315c 100%);
        background-size: 300% 300%;
        animation: heroShift 14s ease-in-out infinite;
        border-radius: 14px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 18px rgba(11, 37, 69, 0.25);
    }
    @keyframes heroShift {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }
    @media (prefers-reduced-motion: reduce) {
        .hero-banner {animation: none;}
    }
    .hero-title {font-size: 1.7rem; font-weight: 700; color: #ffffff; margin: 0;}
    .hero-subtitle {font-size: 0.95rem; color: #cfe3ea; margin-top: 0.3rem;}
    textarea {font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace !important;}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Animated diagrams (Overview → What Makes This "Production-Grade" / Solution
# Architecture tabs): the same plan-then-execute flow every activity
# implements a piece of, drawn as a live diagram instead of static ASCII art.
# Pure inline SVG + CSS, no JS or external assets, so it works the same in
# the sandboxed preview as anywhere else Streamlit renders it.
# ---------------------------------------------------------------------------

# Shared by every diagram below: one CSS block, reused per <svg> so each
# stays a single self-contained string for components.html (its own iframe,
# so identical class names across diagrams never collide).
WF_STYLE_BLOCK = """
<style>
    html, body {margin: 0; padding: 0; background: #ffffff;}
    .wf-line {
        stroke: #1f6f78; stroke-width: 2.5; fill: none;
        stroke-dasharray: 6 7; animation: wf-dash 1.1s linear infinite;
    }
    .wf-line-dashed {
        stroke: #4a5a6a; stroke-width: 1.5; fill: none; stroke-dasharray: 4 4;
    }
    @keyframes wf-dash { to { stroke-dashoffset: -26; } }
    .wf-node rect {
        fill: #eef3f6; stroke: #0b2545; stroke-width: 1.5; rx: 8;
        animation: wf-pulse 3.2s ease-in-out infinite;
    }
    .wf-node.wf-cross rect {
        fill: #f6f1e6; stroke: #93590b; stroke-dasharray: 5 4; animation: none;
    }
    /* Deliberately inert: used for the earlier bootcamps' shapes in the
       three-shapes comparison, so the contrast with this lab's pulsing,
       five-step chain is visual, not just textual. */
    .wf-node.wf-static rect { fill: #f0f0f0; stroke: #8a8a8a; animation: none; }
    .wf-node.wf-static text { fill: #5a5a5a; }
    .wf-line-static {
        stroke: #9a9a9a; stroke-width: 2; fill: none;
    }
    .wf-node text { fill: #0b2545; font: 600 13px sans-serif; text-anchor: middle; }
    .wf-node .wf-sub { font: 400 11px sans-serif; fill: #4a5a6a; }
    .wf-label { font: 500 11px sans-serif; fill: #4a5a6a; text-anchor: middle; }
    .wf-section { font: 700 14px sans-serif; fill: #0b2545; }
    @keyframes wf-pulse {
        0%, 100% { filter: drop-shadow(0 0 0 rgba(31,111,120,0)); }
        50% { filter: drop-shadow(0 0 6px rgba(31,111,120,0.55)); }
    }
    @media (prefers-reduced-motion: reduce) {
        .wf-line { animation: none; }
        .wf-node rect { animation: none; }
    }
</style>
"""

# Three shapes, three bootcamps (Section 6): a single agent, a coordinator
# with two routes, and this lab's Planner driving five specialists.
THREE_SHAPES_SVG = WF_STYLE_BLOCK + """
<svg viewBox="0 0 800 460" style="width:100%; height:auto; max-width:760px; display:block; margin:0.5rem auto;">
    <defs>
        <marker id="wf-arrow4" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#1f6f78"/>
        </marker>
        <marker id="wf-arrow-static2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#9a9a9a"/>
        </marker>
    </defs>

    <text class="wf-section" x="20" y="20">Bootcamp 1: a single agent, straight through</text>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static2)" d="M170,55 L214,55"/>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static2)" d="M470,55 L514,55"/>
    <g class="wf-node wf-static"><rect x="30" y="35" width="140" height="40"/><text x="100" y="60">Query</text></g>
    <g class="wf-node wf-static"><rect x="220" y="35" width="250" height="40"/><text x="345" y="60">CustomerOperationsAgent</text></g>
    <g class="wf-node wf-static"><rect x="524" y="35" width="140" height="40"/><text x="594" y="60">Response</text></g>

    <text class="wf-section" x="20" y="130">Bootcamp 2: a coordinator, two routes</text>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static2)" d="M170,165 L214,165"/>
    <path class="wf-line-static" marker-end="url(#wf-arrow-static2)" d="M380,165 L424,165"/>
    <g class="wf-node wf-static"><rect x="30" y="145" width="140" height="40"/><text x="100" y="170">Query</text></g>
    <g class="wf-node wf-static"><rect x="220" y="145" width="160" height="40"/><text x="300" y="170">Coordinator</text></g>
    <g class="wf-node wf-static"><rect x="434" y="145" width="230" height="40"/><text x="549" y="164">1 of 2 specialists</text><text class="wf-sub" x="549" y="178">Knowledge / Customer Service</text></g>

    <text class="wf-section" x="20" y="235">Bootcamp 3: a planner drives five specialists</text>

    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M400,270 L400,289"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M400,325 L400,344"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M75,398 L75,417"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M220,398 L220,417"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M365,398 L365,417"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M510,398 L510,417"/>
    <path class="wf-line" marker-end="url(#wf-arrow4)" d="M655,398 L655,417"/>

    <g class="wf-node" style="animation-delay:0s"><rect x="320" y="250" width="160" height="40"/><text x="400" y="275">Query</text></g>
    <g class="wf-node" style="animation-delay:0.3s"><rect x="240" y="290" width="320" height="55"/><text x="400" y="313">Planner</text><text class="wf-sub" x="400" y="330">builds the fixed 5-step plan</text></g>
    <g class="wf-node" style="animation-delay:0.6s"><rect x="60" y="345" width="680" height="55"/><text x="400" y="368">Coordinator</text><text class="wf-sub" x="400" y="385">executes each step, accumulating a shared context</text></g>

    <g class="wf-node" style="animation-delay:0.9s"><rect x="15" y="420" width="120" height="35"/><text x="75" y="443" style="font-size:10.5px">Profile</text></g>
    <g class="wf-node" style="animation-delay:0.9s"><rect x="160" y="420" width="120" height="35"/><text x="220" y="443" style="font-size:10.5px">Credit Risk</text></g>
    <g class="wf-node" style="animation-delay:0.9s"><rect x="305" y="420" width="120" height="35"/><text x="365" y="443" style="font-size:10.5px">Compliance</text></g>
    <g class="wf-node" style="animation-delay:0.9s"><rect x="450" y="420" width="120" height="35"/><text x="510" y="443" style="font-size:10.5px">Policy</text></g>
    <g class="wf-node" style="animation-delay:0.9s"><rect x="595" y="420" width="120" height="35"/><text x="655" y="443" style="font-size:10.5px">Recommend</text></g>
</svg>
"""

# Layered architecture (Section 7's first diagram).
ARCHITECTURE_DIAGRAM_SVG = WF_STYLE_BLOCK + """
<svg viewBox="0 0 800 700" style="width:100%; height:auto; max-width:720px; display:block; margin:0.5rem auto;">
    <defs>
        <marker id="wf-arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 z" fill="#1f6f78"/>
        </marker>
    </defs>

    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,60 L400,84"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,140 L400,164"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,220 L400,244"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M280,320 L200,344"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M340,320 L340,344"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M460,320 L480,344"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M520,320 L610,344"/>

    <g class="wf-node" style="animation-delay:0s">
        <rect x="280" y="10" width="240" height="50"/>
        <text x="400" y="32">Presentation</text>
        <text class="wf-sub" x="400" y="48">app/streamlit_app.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.2s">
        <rect x="240" y="90" width="320" height="50"/>
        <text x="400" y="112">Orchestration</text>
        <text class="wf-sub" x="400" y="128">PlannerAgent · src/agents/planner_agent.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.4s">
        <rect x="240" y="170" width="320" height="50"/>
        <text x="400" y="192">Coordination</text>
        <text class="wf-sub" x="400" y="208">AgentCoordinator · src/core/agent_coordinator.py</text>
    </g>
    <g class="wf-node" style="animation-delay:0.6s">
        <rect x="120" y="250" width="560" height="70"/>
        <text x="400" y="272">Reasoning</text>
        <text class="wf-sub" x="400" y="288">5 specialist agents (customer_profile, credit_risk, compliance,</text>
        <text class="wf-sub" x="400" y="302">lending_policy, recommendation) - provided, complete</text>
    </g>

    <g class="wf-node" style="animation-delay:0.8s">
        <rect x="40" y="345" width="240" height="55"/>
        <text x="160" y="367">Protocol Access</text>
        <text class="wf-sub" x="160" y="383">MCP · src/mcp/</text>
    </g>
    <g class="wf-node" style="animation-delay:0.9s">
        <rect x="300" y="345" width="200" height="55"/>
        <text x="400" y="367">Observability</text>
        <text class="wf-sub" x="400" y="383">LangSmith · src/observability/</text>
    </g>
    <g class="wf-node" style="animation-delay:1.0s">
        <rect x="520" y="345" width="240" height="55"/>
        <text x="640" y="367">Validation</text>
        <text class="wf-sub" x="640" y="383">WorkflowValidator · src/core/</text>
    </g>

    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M160,400 L160,424"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,400 L400,424"/>
    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M640,400 L640,424"/>

    <g class="wf-node" style="animation-delay:1.2s">
        <rect x="40" y="430" width="720" height="55"/>
        <text x="400" y="452">Testing &amp; Deployment</text>
        <text class="wf-sub" x="400" y="468">tests/test_workflow.py (pytest) · Dockerfile, docker-compose.yml</text>
    </g>

    <path class="wf-line" marker-end="url(#wf-arrow2)" d="M400,485 L400,509"/>
    <g class="wf-node wf-cross">
        <rect x="40" y="515" width="720" height="55"/>
        <text x="400" y="538">Cross-cutting: reused from Bootcamp 1/2</text>
        <text class="wf-sub" x="400" y="554">config/*.yaml · src/llm/ · src/knowledge/ · src/utils/</text>
    </g>
</svg>
"""


# ---------------------------------------------------------------------------
# Execution + file helpers
# ---------------------------------------------------------------------------

# Bootcamp 3's reference_solution/src is intentionally partial - it "does
# not duplicate shared assets... that already exist once in the main
# project" (README), so it has no utils/, llm/, knowledge/, and no 5
# specialist agents. A plain `sys.path.insert(0, "reference_solution")`
# (Bootcamp 1/2's approach, where reference_solution/src IS a full mirror)
# would shadow the whole `src` package and break every one of those missing
# imports. Build a merged overlay directory instead: a full copy of the
# real src/, config/, and data/ (cached after the first run - the
# specialist agents, utils, and business data never change), with only
# reference_solution's own files copied on top of src/, always fresh. This
# is what the notebook's own commented-out
# `from reference_solution.src.X import Y` alternative achieves too, just
# via a different mechanism (module aliasing vs. a merged directory).
#
# The whole project layout gets mirrored, not just src/, and the *process*
# itself chdirs into the merged copy (not just sys.path), because Activity
# 2.1's MCP client launches its server as a brand-new `python -m
# src.mcp.mcp_server` subprocess - one that resolves its own imports from
# its cwd, inheriting none of this process's in-memory sys.path. Only a
# real cwd change reaches that child process too.
REFERENCE_PATH_PREFIX = """import sys as _sys, os as _os, shutil as _shutil, tempfile as _tempfile
_merge_root = _os.path.join(_tempfile.gettempdir(), "gp3_reference_merge")
_merge_src = _os.path.join(_merge_root, "src")
if not _os.path.isdir(_merge_src):
    _shutil.copytree("src", _merge_src)
    _shutil.copytree("config", _os.path.join(_merge_root, "config"))
    _shutil.copytree("data", _os.path.join(_merge_root, "data"))
for _rel in [
    "agents/planner_agent.py", "core/agent_coordinator.py", "core/workflow_validator.py",
    "mcp/mcp_server.py", "mcp/mcp_client.py", "observability/tracing.py",
    "services/loan_application_service.py", "services/credit_score_service.py",
]:
    _shutil.copy2(_os.path.join("reference_solution", "src", _rel), _os.path.join(_merge_src, _rel))
_sys.path.insert(0, _merge_root)
_os.chdir(_merge_root)
"""


def run_snippet(code: str, timeout: int = 180, use_reference: bool = False) -> dict:
    """Run `code` in a fresh subprocess using this same interpreter, from the
    project root, so every run picks up exactly what's saved on disk right
    now, no module-cache or notebook-kernel staleness possible.

    With use_reference=True, the process chdirs into a merged overlay
    directory instead (real src/, config/, and data/ plus reference_solution's
    own files on top of src/, see REFERENCE_PATH_PREFIX), so every `from
    src...` import resolves to the completed reference implementation for
    the modules this lab's activities implement, and to the real,
    already-complete src/ for everything else (the 5 specialist agents,
    src/utils, src/llm, src/knowledge) - letting a stuck learner see the
    completed solution actually run, not just read its code. The whole
    process moves, not just sys.path, since Activity 2.1's MCP client
    launches its server as a brand-new subprocess that resolves its own
    imports from cwd."""
    code_to_run = (REFERENCE_PATH_PREFIX + code) if use_reference else code
    env = os.environ.copy()
    # Windows defaults a child process's stdout/stderr to the system codepage
    # (cp1252), which crashes on the emoji every activity script prints
    # ([WARN], ✓, ...). Force UTF-8 for the subprocess itself.
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        result = subprocess.run(
            [sys.executable, "-c", code_to_run],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode, "timed_out": False}
    except subprocess.TimeoutExpired as e:
        return {"stdout": e.stdout or "", "stderr": e.stderr or "", "returncode": None, "timed_out": True}


def classify_run(result: dict) -> str:
    if result["timed_out"]:
        return "error"
    if result["returncode"] != 0:
        return "error"
    combined = result["stdout"] + result["stderr"]
    if "NotImplementedError" in combined or "[WARN]" in combined:
        return "warn"
    return "pass"


def read_file(rel_path: str) -> str:
    path = PROJECT_ROOT / rel_path
    if not path.exists():
        return f"# File not found: {rel_path}"
    return path.read_text(encoding="utf-8-sig")


if "activity_status" not in st.session_state:
    st.session_state.activity_status = {}
if "activity_output" not in st.session_state:
    st.session_state.activity_output = {}


# ---------------------------------------------------------------------------
# Activity content: 8 activities across 3 phases (the whole lab)
# ---------------------------------------------------------------------------

ACTIVITIES = [
    dict(
        id="1.1", phase=1, title="Explore the Enterprise Loan Underwriting Platform",
        module="*No module to implement: orientation activity*",
        business_context="""Before extending any enterprise platform, an engineer needs to understand what already exists. The five specialist agents, the mock business data, and the reused knowledge base are already built for you: your job in this lab is the orchestration layer above them.""",
        objective="Locate and understand every module you will implement in this lab, and confirm the provided (complete) specialist agents and business data are in place.",
        instructions="""1. Open `src/agents/` and note the five specialist agents (`customer_profile_agent.py`, `credit_risk_agent.py`, `compliance_agent.py`, `lending_policy_agent.py`, `recommendation_agent.py`): all complete, vendored-style. You will never edit these.
2. Open `src/agents/planner_agent.py` and `src/core/agent_coordinator.py` and read their TODO docstrings: these are what you implement in Activities 1.2 and 1.3.
3. Skim `data/business_data/loan_applications.json` and `data/business_data/credit_scores.json` to see the mock data the specialist agents read.
4. Scroll down and click **Run Activity 1.1** below to load a sample application and confirm all five specialist agent classes import cleanly.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to summarize what each of the five specialist agents' `analyze()` methods returns, from reading their source: useful context for the aggregation logic you write in Activity 1.3.",
        files=[],
        reference_only_files=["config/agent_config.yaml", "config/mcp_config.yaml"],
        milestone="You can explain the platform's architecture and locate every module you'll implement in this lab.",
        validation="""Confirm that:
- 5 mock applications loaded, and the sample application has the fields the specialist agents depend on (`applicant_name`, `loan_type`, `requested_amount`, `annual_income`, `existing_emis`, `kyc_status`)
- All 5 specialist agent classes imported without error""",
        pass_label="✓ Orientation check complete: nothing to implement here yet",
        script="""import json
from pathlib import Path

from src.agents.customer_profile_agent import CustomerProfileAgent
from src.agents.credit_risk_agent import CreditRiskAgent
from src.agents.compliance_agent import ComplianceAgent
from src.agents.lending_policy_agent import LendingPolicyAgent
from src.agents.recommendation_agent import RecommendationAgent

applications = json.load(open("data/business_data/loan_applications.json", encoding="utf-8"))["applications"]
sample = applications[0]

print(f"Loaded {len(applications)} mock loan applications. Sample:")
print(json.dumps(sample, indent=2))

specialist_agents = [CustomerProfileAgent, CreditRiskAgent, ComplianceAgent, LendingPolicyAgent, RecommendationAgent]
print(f"\\n✓ All {len(specialist_agents)} specialist agent classes imported successfully: "
      + ", ".join(a.__name__ for a in specialist_agents))
""",
    ),
    dict(
        id="1.2", phase=1, title="Implement the Planner Agent",
        module="`src/services/loan_application_service.py`, `src/services/credit_score_service.py`, `src/agents/planner_agent.py`",
        business_context="""Before any agent can reason about a loan application, the platform needs a plan, and to be able to look up the application and credit data every specialist agent depends on. Getting this wrong (e.g. silently building a plan for an application that doesn't exist) would send a bad application five agents deep before anyone noticed.""",
        objective="Implement the two loan-domain data lookups and the Planner's fixed, linear plan builder.",
        concept_overview="""The **Planner pattern**: a component whose only job is deciding *what work needs to happen and in what order*, not doing any of the work itself. This lab's planner is intentionally the simplest illustrative case: one fixed plan (Customer Profile → Credit Risk → Compliance → Lending Policy → Recommendation) for every application, not a dynamic planner that reasons about which steps to skip.""",
        instructions="""1. In `src/services/loan_application_service.py`, implement `get_loan_application()`: load `loan_applications.json`, search by `application_id`, return the match or a `{"error": ...}` dict.
2. In `src/services/credit_score_service.py`, implement `get_credit_score()` the same way against `credit_scores.json`, keyed by `customer_id`.
3. In `src/agents/planner_agent.py`, implement `PlannerAgent.build_plan()`: validate the application exists (via `get_loan_application()`, raising `ValueError` if it returns an `"error"` key), then return the 5-step ordered plan, one dict per name in `self.sequence`, shaped `{"step": <1-based index>, "agent": <step name>, "application_id": application_id}`.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to explain why validating the application exists *before* building the plan (rather than after) avoids wasted work downstream.",
        files=["src/services/loan_application_service.py", "src/services/credit_score_service.py", "src/agents/planner_agent.py"],
        target_methods={
            "src/services/loan_application_service.py": ["get_loan_application"],
            "src/services/credit_score_service.py": ["get_credit_score"],
            "src/agents/planner_agent.py": ["build_plan"],
        },
        milestone="The Planner Agent produces a valid execution plan for a loan application.",
        validation="""Confirm that:
- The plan has exactly 5 steps, in this exact order: `customer_profile`, `credit_risk`, `compliance`, `lending_policy`, `recommendation`
- Every step's `application_id` matches `LOAN-5001`
- Try `planner.build_plan("LOAN-9999")` (a non-existent ID) separately and confirm it raises a `ValueError` rather than building a plan for nothing""",
        script="""from src.agents.planner_agent import PlannerAgent
from src.services.loan_application_service import get_loan_application

APPLICATION_ID = "LOAN-5001"

try:
    planner = PlannerAgent()
    plan = planner.build_plan(APPLICATION_ID)
    print(f"Plan for {APPLICATION_ID} ({len(plan)} steps):")
    for step in plan:
        print(f"  {step}")

    expected_order = ["customer_profile", "credit_risk", "compliance", "lending_policy", "recommendation"]
    got_order = [step.get("agent") for step in plan]
    if got_order != expected_order:
        print(f"[WARN] Expected steps in order {expected_order}, got {got_order}")
    bad_ids = [step for step in plan if step.get("application_id") != APPLICATION_ID]
    if bad_ids:
        print(f"[WARN] Every step's application_id should be {APPLICATION_ID!r}, found mismatches: {bad_ids}")

    try:
        planner.build_plan("LOAN-9999")
        print("[WARN] build_plan('LOAN-9999') should have raised ValueError for a non-existent application")
    except ValueError:
        print("✓ build_plan('LOAN-9999') correctly raised ValueError for a non-existent application")
except NotImplementedError as e:
    print(f"[WARN] Not implemented yet: {e}")
    print("Complete src/services/loan_application_service.py, "
          "src/services/credit_score_service.py, and src/agents/planner_agent.py first.")
""",
    ),
    dict(
        id="1.3", phase=1, title="Coordinate Specialized AI Agents",
        module="`src/core/agent_coordinator.py`",
        business_context="""A plan is only useful if something actually executes it. The Coordinator is the "connect what's provided" layer: it wires the five already-complete specialist agents into named steps and runs a Planner-built plan against them: it never reimplements any agent's internal reasoning.""",
        objective="Implement `AgentCoordinator.run_workflow()` so a full loan application runs end-to-end through all five specialist agents and returns one aggregated result.",
        concept_overview="""**Advanced multi-agent orchestration**: each step's output is added to a shared `context` dict passed to the *next* step, so later agents (especially Recommendation) can read what earlier agents found: the same accumulate-as-you-go shape a real multi-agent workflow needs, kept to one clean, fixed sequence per this lab's scope.

This activity's specialist agents make real OpenAI API calls: it needs a configured `OPENAI_API_KEY` to run to completion.""",
        instructions="""In `src/core/agent_coordinator.py`, implement `run_workflow()`:
1. Call `self.planner.build_plan(application_id)` to get the ordered list of step dicts (each has `"agent"` and `"application_id"` keys).
2. Create an empty `results: Dict[str, Any] = {}` accumulator.
3. For each step in the plan, in order: look up the callable in `self.steps` by `step["agent"]` (raise `KeyError` naming the missing step if it isn't registered), call it as `callable(application_id=application_id, context=results)`, passing everything accumulated so far, and store the returned dict under `results[step["agent"]]`.
4. Return `results`, keyed by agent name: `customer_profile`, `credit_risk`, `compliance`, `lending_policy`, `recommendation`, the exact shape `src/core/workflow_validator.py` checks in Activity 2.3.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to trace through what `context` looks like immediately before the `\"recommendation\"` step runs, given the other four steps' return shapes.",
        files=["src/core/agent_coordinator.py"],
        target_methods={"src/core/agent_coordinator.py": ["run_workflow"]},
        milestone="The Planner successfully coordinates all 5 specialist agents and aggregates their outputs into one workflow result.",
        validation="""Confirm that:
- All 5 section keys (`customer_profile`, `credit_risk`, `compliance`, `lending_policy`, `recommendation`) are present in `result`
- `result["recommendation"]["decision"]` is one of `Approve`, `Refer`, `Decline`
- Try a second application ID (e.g. `LOAN-5003`, which has `kyc_status: "Pending"`) and notice how the Compliance section's output differs""",
        script="""from src.agents.planner_agent import PlannerAgent
from src.core.agent_coordinator import AgentCoordinator

APPLICATION_ID = "LOAN-5001"

try:
    coordinator = AgentCoordinator()
    result = coordinator.run_workflow(APPLICATION_ID)
    print("Workflow result sections:", list(result.keys()))
    print(f"\\nFinal decision: {result.get('recommendation', {}).get('decision')}")
    print(result.get("recommendation", {}).get("rationale"))

    expected_sections = {"customer_profile", "credit_risk", "compliance", "lending_policy", "recommendation"}
    missing = expected_sections - set(result.keys())
    if missing:
        print(f"[WARN] Missing expected section(s): {sorted(missing)}")
    decision = result.get("recommendation", {}).get("decision")
    if decision not in ("Approve", "Refer", "Decline"):
        print(f"[WARN] Expected decision to be one of Approve/Refer/Decline, got {decision!r}")
except NotImplementedError as e:
    print(f"[WARN] Not implemented yet: {e}")
    print("Complete src/core/agent_coordinator.py first.")
""",
    ),
    dict(
        id="2.1", phase=2, title="Integrate MCP",
        module="`src/mcp/mcp_server.py`, `src/mcp/mcp_client.py`",
        business_context="""Enterprise platforms need a standardized way for agents and tools to talk to each other, instead of every integration being ad hoc. The Model Context Protocol (MCP) is that standard. This lab wraps exactly one existing capability, the credit bureau lookup you already implemented in Activity 1.2, as a single MCP tool, so you experience the protocol end-to-end without migrating the whole tool surface.""",
        objective="Expose `get_credit_score()` as an MCP tool, and implement the client call site that invokes it over MCP.",
        concept_overview="""MCP has two sides: a **server** that registers tools and answers calls, and a **client** that connects to a server (here, over a local `stdio` subprocess, no network involved) and invokes a named tool. This lab uses `mcp.server.fastmcp.FastMCP` for the server side and `mcp.ClientSession` for the client side.""",
        instructions="""1. In `src/mcp/mcp_server.py`, implement `get_credit_score_tool()`: a one-line delegation to `get_credit_score()` (the FastMCP server instance and `@mcp_app.tool()` registration are already prefilled).
2. In `src/mcp/mcp_client.py`, implement `_call_get_credit_score()`: launch the server over stdio, open a session, call the tool, and parse its result, following the docstring's numbered steps.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to explain the difference between MCP `stdio` transport (used here) and `http`/`sse` transport (used when the server runs as a separate long-lived process), and why `stdio` is the right choice for this lab's single-tool example.",
        files=["src/mcp/mcp_server.py", "src/mcp/mcp_client.py"],
        target_methods={
            "src/mcp/mcp_server.py": ["get_credit_score_tool"],
            "src/mcp/mcp_client.py": ["_call_get_credit_score"],
        },
        milestone="The platform exposes at least one enterprise capability through a standardized MCP tool interface.",
        validation="""Confirm that:
- `mcp_result` matches `CUST-1001`'s record in `credit_scores.json` (`credit_score`, `bureau`, `delinquencies`, `credit_utilization_pct`)
- No exception is raised other than `NotImplementedError` if you haven't finished the TODOs yet: a real MCP round-trip (subprocess launch, session handshake, tool call) succeeding end-to-end is the pass signal here, there's no separate simulated-vs-real mode""",
        script="""from src.mcp.mcp_client import fetch_credit_score_via_mcp
from src.services.credit_score_service import get_credit_score

try:
    mcp_result = fetch_credit_score_via_mcp("CUST-1001")
    print("Credit score fetched via MCP:")
    print(mcp_result)

    direct_result = get_credit_score("CUST-1001")
    if mcp_result != direct_result:
        print(f"[WARN] MCP round-trip result differs from the direct service call: {mcp_result} vs {direct_result}")
    else:
        print("✓ MCP round-trip result matches CUST-1001's record in credit_scores.json")
except NotImplementedError as e:
    print(f"[WARN] Not implemented yet: {e}")
    print("Complete src/mcp/mcp_server.py and src/mcp/mcp_client.py first.")
""",
    ),
    dict(
        id="2.2", phase=2, title="Enable LangSmith Observability",
        module="`src/observability/tracing.py`",
        business_context="""A production platform's engineers need to see what a multi-agent workflow actually did: which steps ran, what each one returned, how long it took, without reading raw logs. LangSmith gives you that for free once a run is wrapped in tracing.""",
        objective="Wrap a full Planner-driven workflow run in LangSmith tracing.",
        concept_overview="""LangSmith tracing here is two environment variables (`LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`) plus wrapping **one** orchestration entry point, not custom dashboards or evaluation datasets. `configure_langsmith()` (already implemented) reads those two variables; your job is the wrapping itself.

If you have a LangSmith API key, set `LANGCHAIN_TRACING_V2=true` and your real `LANGCHAIN_API_KEY` in `.env` before running this activity to see a live trace. Without one, it still runs correctly **and prints a local step-by-step trace to stdout** (via the prefilled `_run_with_local_trace()` helper), so this activity always produces a visible trace artifact. LangSmith is optional infrastructure, not a hard requirement to complete this lab.""",
        instructions="""In `src/observability/tracing.py`, implement `run_planner_with_tracing()`: check `configure_langsmith()`, then either run it via the prefilled `_run_with_local_trace(run_fn, *args, **kwargs)` helper (untraced - still prints a local trace) or wrap it with `langsmith.traceable()` first, and return that call's result.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant what `langsmith.traceable()` actually does to the wrapped function's call, and why returning the *wrapped* callable's result (not the original) matters.",
        files=["src/observability/tracing.py"],
        target_methods={"src/observability/tracing.py": ["run_planner_with_tracing"]},
        milestone="A full Planner run is traced and visible in LangSmith.",
        validation="""Confirm that:
- The run prints a decision either way (traced or untraced): tracing being off must never break the workflow
- Without LangSmith configured, a local step-by-step trace prints (each agent, in order, with what it produced) - that is the visible artifact for this activity
- If you configured real LangSmith credentials, check https://smith.langchain.com under project `loan-underwriting-platform` and confirm the run appears there as `loan_underwriting_planner_run`""",
        script="""from src.core.agent_coordinator import AgentCoordinator
from src.observability.tracing import run_planner_with_tracing

APPLICATION_ID = "LOAN-5001"

try:
    coordinator = AgentCoordinator()
    traced_result = run_planner_with_tracing(coordinator.run_workflow, APPLICATION_ID)
    print("Traced run completed. Decision:", traced_result.get("recommendation", {}).get("decision"))
    print("If LANGCHAIN_TRACING_V2=true and a real LANGCHAIN_API_KEY are set, "
          "check https://smith.langchain.com for this run under project "
          "'loan-underwriting-platform'.")
except NotImplementedError as e:
    print(f"[WARN] Not implemented yet: {e}")
    print("Complete src/observability/tracing.py first.")
""",
    ),
    dict(
        id="2.3", phase=2, title="Validate Multi-Agent Workflows",
        module="`src/core/workflow_validator.py`",
        business_context="""Before a workflow's recommendation reaches a loan officer, the platform should catch a malformed result itself, a missing section, an unrecognized decision value, rather than surface a broken response.""",
        objective="Implement structural, in-workflow validation of a workflow result's shape.",
        instructions="""In `src/core/workflow_validator.py`, implement `WorkflowValidator.validate()`: check every required section is present and is a dict, then check the final decision is one of the allowed values (`Approve`, `Refer`, `Decline`).""",
        ai_assist="**AI Assist:** Ask your AI coding assistant for two or three additional structural checks a production version of this validator might add (e.g. citation non-emptiness): you don't need to implement them, just understand where this validator's scope deliberately stops.",
        files=["src/core/workflow_validator.py"],
        target_methods={"src/core/workflow_validator.py": ["validate"]},
        milestone="The platform validates a multi-agent workflow's output shape before returning it.",
        validation="""Confirm that:
- `good_errors` is `None` for a real workflow result
- `bad_errors` is a non-empty list flagging the missing sections (`credit_risk`, `compliance`, `lending_policy`) and the invalid decision value `"Maybe"`""",
        script="""from src.agents.planner_agent import PlannerAgent
from src.core.agent_coordinator import AgentCoordinator
from src.core.workflow_validator import WorkflowValidator

APPLICATION_ID = "LOAN-5001"

try:
    coordinator = AgentCoordinator()
    result = coordinator.run_workflow(APPLICATION_ID)
except NotImplementedError as e:
    print(f"[WARN] Cannot proceed: Activity 1.3 not complete yet ({e})")
    result = None

try:
    validator = WorkflowValidator()

    if result is not None:
        good_errors = validator.validate(result)
        print("Validation errors on the real workflow result:", good_errors)
        if good_errors is not None:
            print(f"[WARN] Expected None for a well-formed workflow result, got {good_errors!r}")

    broken_result = {"customer_profile": {}, "recommendation": {"decision": "Maybe"}}
    bad_errors = validator.validate(broken_result)
    print("Validation errors on a deliberately broken result:", bad_errors)
    if not bad_errors:
        print("[WARN] Expected a non-empty list of errors for the deliberately broken result, got none")
    else:
        errors_text = " ".join(str(e) for e in bad_errors)
        for missing_section in ("credit_risk", "compliance", "lending_policy"):
            if missing_section not in errors_text:
                print(f"[WARN] Expected the missing section '{missing_section}' to be flagged, wasn't found in: {bad_errors}")
        if "Maybe" not in errors_text and "decision" not in errors_text.lower():
            print(f"[WARN] Expected the invalid decision 'Maybe' to be flagged, wasn't found in: {bad_errors}")
except NotImplementedError as e:
    print(f"[WARN] Not implemented yet: {e}")
    print("Complete src/core/workflow_validator.py first.")
""",
    ),
    dict(
        id="3.1", phase=3, title="Implement Automated Testing",
        module="`tests/test_workflow.py`",
        business_context="""Manually re-running notebook cells doesn't scale as a regression check. A small, automated pytest suite lets the team (and CI) confirm the platform's structural behavior hasn't broken, in seconds, without any manual review.""",
        objective="Implement the three TODO tests in `tests/test_workflow.py` (the other two are prefilled structural checks).",
        concept_overview="""This is a **small, fixed smoke suite**: it checks shape (plan length, step names, registry keys, validator behavior), not LLM output quality. None of these tests call the real OpenAI API, so they run even without a configured key.""",
        instructions="""In `tests/test_workflow.py`, implement `test_planner_builds_expected_plan`, `test_agent_coordinator_registers_all_steps`, and `test_workflow_validator_flags_missing_sections`, following each docstring's numbered steps.""",
        ai_assist="**AI Assist:** Ask your AI coding assistant to explain why these tests avoid calling `.analyze()` on the real specialist agents: what would that trade away (speed, determinism, offline-runnability) that a structural test suite is meant to preserve?",
        files=["tests/test_workflow.py"],
        target_methods={"tests/test_workflow.py": [
            "test_planner_builds_expected_plan",
            "test_agent_coordinator_registers_all_steps",
            "test_workflow_validator_flags_missing_sections",
        ]},
        milestone="A pytest suite automatically validates the platform's workflow behavior.",
        validation="""Confirm that:
- All 5 tests in `tests/test_workflow.py` pass (`5 passed` in pytest's summary line)
- Re-read any test that fails: the failure message names the exact assertion that didn't hold""",
        script="""# Activity 3.1: run the pytest smoke suite. This never raises itself; it
# reports pytest's own pass/fail in the printed output instead, with an
# explicit warning marker on any failure so the app's own pass/warn/error
# status picks it up correctly either way.
import subprocess
import sys

proc = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_workflow.py", "-v"],
    capture_output=True, text=True,
)
print(proc.stdout[-4000:])
if proc.returncode != 0:
    print(proc.stderr[-2000:])
    print(f"\\n[WARN] pytest exited with code {proc.returncode}: complete the TODO tests in tests/test_workflow.py.")
else:
    print("\\n✓ pytest suite passed.")
""",
    ),
    dict(
        id="3.2", phase=3, title="Containerize the Platform",
        module="*No module to implement: build and run the provided Dockerfile*",
        business_context="""A platform that only runs "on my machine" isn't enterprise-ready. Docker packages the whole platform (code, dependencies, runtime) into one reproducible artifact any environment can run identically.""",
        objective="Build the provided Docker image, run it, and confirm the portal is reachable inside the container.",
        instructions="""There's no code cell for this activity: Docker build/run happens in your terminal, not inside this app.
1. From the project root, run `docker build -t loan-underwriting-platform .` (or `docker compose build`).
2. Run `docker compose up` (this reads your `.env` file via `env_file:` in `docker-compose.yml`: confirm `.env` exists first).
3. Open `http://localhost:8502` in a browser and confirm the Enterprise Loan Underwriting Portal loads inside the container. (The container maps host port **8502** to container 8501, so it won't clash with this workbook app or a local `streamlit run` on 8501.)
4. Click **Run Activity 3.2** below only after the container is up, to confirm the health endpoint responds from your host machine.
5. Stop the container with `docker compose down` when you're done.""",
        ai_assist="**AI Assist:** If `docker build` fails, paste the exact error into your AI coding assistant along with the `Dockerfile`: most first-time Docker build failures on a new machine are missing system dependencies or a stale image cache, not something wrong with this project's code.",
        files=[],
        reference_only_files=["Dockerfile", "docker-compose.yml"],
        milestone="The platform runs successfully inside a Docker container.",
        validation="""Confirm that:
- The health check reports a successful response once the container is running
- The portal at `http://localhost:8502` looks and behaves the same as when run locally with `streamlit run app/streamlit_app.py`
- A workflow run inside the container succeeds, meaning your `OPENAI_API_KEY` reached the container correctly via `.env` passthrough""",
        script="""# Activity 3.2: verify the containerized portal is reachable. Run this
# AFTER `docker compose up`, from your host machine. The container publishes
# on host port 8502 (-> container 8501), per docker-compose.yml.
import urllib.request
import urllib.error

try:
    with urllib.request.urlopen("http://localhost:8502/_stcore/health", timeout=5) as resp:
        print(f"✓ Container health check responded with status {resp.status}.")
except (urllib.error.URLError, ConnectionRefusedError, TimeoutError) as e:
    print(f"[WARN] Could not reach the container at localhost:8502 ({e}).")
    print("   Run `docker compose up` in a terminal first, then re-run this check.")
""",
    ),
]

ACTIVITIES_BY_ID = {a["id"]: a for a in ACTIVITIES}
PHASE_TITLES = {
    1: "Phase 1 · Planner-Driven Orchestration",
    2: "Phase 2 · Protocol, Observability, and Structural Validation",
    3: "Phase 3 · Testing and Containerization",
}
PHASE_INTRO = {
    1: dict(
        objective="Stand up the Planner/Coordinator pattern that drives every loan application through the "
                  "five specialist agents.",
        outcome="By the end of this phase, a full loan application can be run end-to-end through all five "
                "specialist agents and return one aggregated result.",
    ),
    2: dict(
        objective="Give the platform a standardized tool interface, make its runs traceable, and have it "
                  "check its own output before returning it.",
        outcome="By the end of this phase, one enterprise capability is reachable over MCP, a full Planner "
                "run is visible in LangSmith, and the workflow validates its own result shape.",
    ),
    3: dict(
        objective="Give the platform automated tests and confirm it runs inside a container.",
        outcome="By the end of this phase, an automated test suite passes against your implementation and the "
                "platform runs inside Docker.",
    ),
}

# Short, single-line labels for the sidebar nav: the full descriptive title
# (used in PAGES, the hero banner, and Prev/Next buttons) wraps to 2-3 lines
# in the narrow sidebar and, repeated for all 8 activities, buries the actual
# navigation under a wall of text. The nav only needs enough to recognize
# "where am I"; the full title is one click away on the activity page itself.
NAV_SHORT_TITLES = {
    "1.1": "Explore the Platform",
    "1.2": "Implement the Planner Agent",
    "1.3": "Coordinate Specialist Agents",
    "2.1": "Integrate MCP",
    "2.2": "Enable LangSmith Observability",
    "2.3": "Validate Multi-Agent Workflows",
    "3.1": "Implement Automated Testing",
    "3.2": "Containerize the Platform",
}

REFERENCE_MAP = {
    "src/agents/planner_agent.py": "reference_solution/src/agents/planner_agent.py",
    "src/core/agent_coordinator.py": "reference_solution/src/core/agent_coordinator.py",
    "src/mcp/mcp_server.py": "reference_solution/src/mcp/mcp_server.py",
    "src/mcp/mcp_client.py": "reference_solution/src/mcp/mcp_client.py",
    "src/observability/tracing.py": "reference_solution/src/observability/tracing.py",
    "src/core/workflow_validator.py": "reference_solution/src/core/workflow_validator.py",
    "src/services/loan_application_service.py": "reference_solution/src/services/loan_application_service.py",
    "src/services/credit_score_service.py": "reference_solution/src/services/credit_score_service.py",
    "tests/test_workflow.py": "reference_solution/tests/test_workflow.py",
}


# ---------------------------------------------------------------------------
# Sidebar: navigation + progress tracker
# ---------------------------------------------------------------------------

PAGES = ["Overview & Setup"] + [f"Activity {a['id']} · {a['title']}" for a in ACTIVITIES] + ["Final Review"]

# Two-level nav: a top-level segmented control for Overview / each Phase /
# Final Review, then (only for a Phase) a short radio scoped to that
# phase's 3 activities. This keeps the always-visible list to at most 5
# items instead of all 11 activities at once, without the duplicate-selector
# trap other tools fall into (two separate widgets both choosing the same
# activity); this radio is the *only* control for "which activity."
TOP_LEVEL_OPTIONS = ["Overview"] + [f"Phase {p}" for p in PHASE_TITLES] + ["Final Review"]


def _nav_label(page: str) -> str:
    if page.startswith("Activity "):
        activity_id = page.replace("Activity ", "").split(" · ")[0]
        return f"{activity_id}  {NAV_SHORT_TITLES.get(activity_id, '')}"
    return page


def _phase_pages(phase_num: int) -> list:
    return [f"Activity {a['id']} · {a['title']}" for a in ACTIVITIES if a["phase"] == phase_num]


def _top_level_for(page: str) -> str:
    if page == PAGES[0] or page == PAGES[-1]:
        return TOP_LEVEL_OPTIONS[0] if page == PAGES[0] else TOP_LEVEL_OPTIONS[-1]
    activity_id = page.replace("Activity ", "").split(" · ")[0]
    return f"Phase {ACTIVITIES_BY_ID[activity_id]['phase']}"


if "nav_top" not in st.session_state:
    st.session_state.nav_top = TOP_LEVEL_OPTIONS[0]
# Widget session_state keys can't be reassigned after that widget has
# already been instantiated in the same run, so Previous/Next buttons
# (below) stage their target page here, applied before the widgets run.
if "pending_nav" in st.session_state:
    target = st.session_state.pop("pending_nav")
    st.session_state.nav_top = _top_level_for(target)
    if target not in (PAGES[0], PAGES[-1]):
        phase_num = ACTIVITIES_BY_ID[target.replace("Activity ", "").split(" · ")[0]]["phase"]
        st.session_state[f"nav_sub_{phase_num}"] = target

with st.sidebar:
    st.header("Guided Workbook")
    top_choice = st.segmented_control(
        "Section", TOP_LEVEL_OPTIONS, label_visibility="collapsed", key="nav_top"
    )
    if top_choice is None:
        # Clicking the active segment again deselects it in Streamlit. A
        # widget's session_state key can't be reassigned after that widget
        # has already run in this script pass, so defer the reset to
        # Overview via the same pending_nav mechanism the Previous/Next
        # buttons use (handled at the top of this block, before any widget
        # runs) and start a fresh run.
        st.session_state.pending_nav = PAGES[0]
        st.rerun()

    if top_choice in (TOP_LEVEL_OPTIONS[0], TOP_LEVEL_OPTIONS[-1]):
        selected_page = PAGES[0] if top_choice == TOP_LEVEL_OPTIONS[0] else PAGES[-1]
    else:
        phase_num = int(top_choice.split()[-1])
        phase_pages = _phase_pages(phase_num)
        sub_key = f"nav_sub_{phase_num}"
        if sub_key not in st.session_state:
            st.session_state[sub_key] = phase_pages[0]
        st.caption(f"↳ Activities in {top_choice}")
        selected_page = st.radio(
            "Activity", phase_pages, format_func=_nav_label, label_visibility="collapsed", key=sub_key
        )

    st.divider()
    st.subheader("Progress")

    passed_count = sum(1 for a in ACTIVITIES if st.session_state.activity_status.get(a["id"]) == "pass")
    total_count = len(ACTIVITIES)
    st.metric("Activities Complete", f"{passed_count} / {total_count}")
    st.progress(passed_count / total_count, text=f"{round(100 * passed_count / total_count)}% complete")

    if passed_count == total_count and not st.session_state.get("celebrated"):
        st.session_state.celebrated = True
        st.balloons()

    st.write("")
    for phase, phase_title in PHASE_TITLES.items():
        phase_activities = [a for a in ACTIVITIES if a["phase"] == phase]
        phase_done = sum(1 for a in phase_activities if st.session_state.activity_status.get(a["id"]) == "pass")
        st.caption(f"{phase_title.split('·')[0].strip()} · {phase_done}/{len(phase_activities)}")
        st.progress(phase_done / len(phase_activities))


# ---------------------------------------------------------------------------
# Reusable page pieces
# ---------------------------------------------------------------------------

def render_file_hint(rel_path: str):
    ref_path = REFERENCE_MAP.get(rel_path)
    if ref_path and (PROJECT_ROOT / ref_path).exists():
        with st.expander(f"Need a hint? View reference solution for {rel_path}"):
            st.code(read_file(ref_path), language="python")


def extract_method_source(file_text: str, method_name: str) -> tuple[str | None, str | None]:
    """Pull just one function/method's exact source (decorators included)
    out of a file's current text via ast, rather than the whole file, so
    the highlight below stays scoped to the few lines a participant is
    actually meant to touch. Returns (code, error): code is None if the
    file doesn't parse (a participant mid-edit with a syntax error) or the
    name isn't found; error carries the real SyntaxError detail so it can
    be shown instead of a generic "not found" message."""
    try:
        tree = ast.parse(file_text)
    except SyntaxError as e:
        return None, f"{e.msg} at line {e.lineno}, column {e.offset}"
    lines = file_text.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method_name:
            start_line = min([node.lineno] + [d.lineno for d in node.decorator_list])
            return "\n".join(lines[start_line - 1:node.end_lineno]), None
    return None, None


def render_code_to_work_on(rel_path: str, method_names: list):
    """Live, read-only view of exactly the method(s) an activity asks the
    participant to implement, extracted fresh from their current src/ file
    on every render, isolated from the surrounding file so the ~10-30 lines
    that matter aren't buried in a full-file dump."""
    label_col, refresh_col = st.columns([5, 1])
    label_col.markdown("**Code you'll work on**: live from your current file, not the answer.")
    # This block only re-reads the file on a Streamlit rerun (any widget
    # interaction), saving in VS Code alone doesn't trigger one, so it can
    # sit stale while you're just looking at the page. Clicking anything
    # reruns the whole script anyway (read_file() below always re-reads
    # from disk); this button exists so there's something to click even
    # when you haven't touched any other widget.
    refresh_col.button("Refresh", key=f"refresh_code_{rel_path}", help="Re-check this file's status against what's currently saved on disk.")
    text = read_file(rel_path)
    for name in method_names:
        segment, error = extract_method_source(text, name)
        if segment is None:
            if error:
                st.caption(f"`{name}`: can't check TODO status yet - {error} in {rel_path}. Fix this first, then the ✓/○ status below will work again.")
            else:
                st.caption(f"`{name}` not found in {rel_path} (it's been renamed or removed).")
            continue
        # Most stubs signal "not done" with `raise NotImplementedError`, but
        # a couple only leave a `# TODO:` comment behind, check for both, or
        # a half-finished method reads as done.
        done = "raise NotImplementedError" not in segment and "TODO" not in segment
        st.caption(f"{'✓' if done else '○'} `{name}`" + (": looks implemented" if done else ": still has a TODO"))
        st.code(segment, language="python")


STATUS_LABEL = {
    "pass": "✓ All checks passed",
    "warn": "[WARN] Not fully implemented yet",
    "error": "✗ The script raised an error",
}


def status_label_for(activity: dict, status: str) -> str:
    if status == "pass" and activity.get("pass_label"):
        return activity["pass_label"]
    return STATUS_LABEL.get(status, "Done")


def render_activity_runner(activity: dict):
    st.markdown("### Run & Validate")
    # The "See reference solution run" button re-runs this activity's own
    # check against reference_solution/. It only makes sense when the check
    # imports from src (something the participant built): 3.1's pytest
    # subprocess and 3.2's Docker health check don't, so they get no run
    # button. 3.1 still gets a "View reference solution" hint
    # (reference_solution/tests/test_workflow.py) via REFERENCE_MAP; 3.2 has
    # no reference_solution counterpart at all.
    has_reference_run = "from src" in activity["script"] or "import src" in activity["script"]

    if has_reference_run:
        run_col, ref_col = st.columns(2)
    else:
        run_col = st.container()
    run_clicked = run_col.button(f"> Run Activity {activity['id']}", type="primary", key=f"run_{activity['id']}")
    ref_clicked = has_reference_run and ref_col.button(
        "See reference solution run", key=f"ref_{activity['id']}",
        help="Runs this same check against the completed reference_solution/ instead of your src/. "
             "Use it if you're stuck and want to see what passing actually looks like. "
             "Doesn't count toward your progress."
    )

    if ref_clicked:
        with st.status("Running against reference_solution/ ...", expanded=True):
            result = run_snippet(activity["script"], use_reference=True)
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
        st.session_state[f"reference_output_{activity['id']}"] = result
    elif f"reference_output_{activity['id']}" in st.session_state:
        with st.status("Reference solution output", expanded=False):
            result = st.session_state[f"reference_output_{activity['id']}"]
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")

    if run_clicked:
        with st.status("Running against your current src/ code...", expanded=True) as status_box:
            result = run_snippet(activity["script"])
            status = classify_run(result)
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
            if result["timed_out"]:
                status_box.update(label="Timed out", state="error", expanded=True)
            else:
                status_box.update(
                    label=status_label_for(activity, status),
                    state="complete" if status == "pass" else ("error" if status == "error" else "complete"),
                    expanded=(status != "pass"),
                )
        st.session_state.activity_status[activity["id"]] = status
        st.session_state.activity_output[activity["id"]] = result
        # Rerun so the sidebar's progress tracker (rendered earlier in script
        # order, before this activity page) picks up the status set just now.
        st.rerun()

    elif activity["id"] in st.session_state.activity_output:
        # Re-show the last run's result on a fresh page load, without re-running it.
        result = st.session_state.activity_output[activity["id"]]
        status = st.session_state.activity_status.get(activity["id"])
        with st.status(status_label_for(activity, status), state="complete" if status == "pass" else "error", expanded=(status != "pass")):
            output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
            st.code(output.strip() or "(no output)", language="text")
        if status == "pass":
            st.success("Milestone reached: you're ready for the next activity.")

    if activity.get("validation"):
        # Collapsed by default: this is what to check in your own output
        # beyond "did it run," most useful once you actually have output to
        # read it against, not before.
        with st.expander("✓ How to check your result"):
            st.markdown(activity["validation"])


# ---------------------------------------------------------------------------
# Page: Overview & Setup
# ---------------------------------------------------------------------------

if selected_page == "Overview & Setup":
    st.markdown("""
    <div class="hero-banner">
        <p class="hero-title">Guided Project: Enterprise Loan Underwriting Platform</p>
        <p class="hero-subtitle">Retail Banking · Loan Underwriting Operations · Bootcamp 3, Production Multi-Agent Systems</p>
    </div>
    """, unsafe_allow_html=True)

    # These facts are fixed for the whole session (not a live metric to
    # track), so a caption (not st.metric) is the honest way to show them:
    # a metric implies "watch this change," which this never does.
    st.caption(
        f"{len(ACTIVITIES)} activities · {len(PHASE_TITLES)} phases · ~3 hrs · 5 specialist agents · MCP + LangSmith + pytest + Docker"
    )

    st.markdown("""
Welcome. You are joining the Enterprise AI Platform Engineering team at a retail bank that has just deployed
the Bootcamp 2 Customer Service Operations Platform. The bank's next phase is a **Production-Ready Enterprise
Loan Underwriting Platform**: a Planner Agent that orchestrates five specialized agents, communicates with
enterprise tools through the Model Context Protocol, is observable via LangSmith, is validated by automated
tests, and is packaged for deployment. In this lab you build that platform, not as a prototype, but with the
operational discipline a production system needs.

The project structure, UI, config, and data are already built; your job is the orchestration, protocol,
observability, testing, and deployment layers, one guided activity at a time.
""")

    if st.button("Start Activity 1.1: Explore the Platform", type="primary", use_container_width=True):
        st.session_state.pending_nav = PAGES[1]
        st.rerun()

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["Business Context & Objectives", "What Makes This \"Production-Grade\"", "Solution Architecture"])

    with tab1:
        with st.container(border=True):
            st.markdown("##### What You'll Build")
            st.markdown("""
- A `PlannerAgent` that builds a fixed, linear execution plan across five specialist agents
- An `AgentCoordinator` that wires those agents into invokable steps and executes the plan end-to-end
- One enterprise capability (credit bureau lookup) exposed through a Model Context Protocol tool, with a working client call site
- A LangSmith-traced orchestration entry point
- A `WorkflowValidator` that checks a workflow result's shape before it is returned
- A pytest smoke suite validating the platform's structural behavior
- A platform verified to run inside Docker
""")
            st.caption("Built incrementally across 8 guided activities in 3 phases, each validated before you move on.")

        with st.container(border=True):
            st.markdown("##### The Business Problem")
            st.markdown("""
Loan underwriting is a fundamentally different shape of work than customer service: it requires several
specialized judgments (customer profile analysis, credit risk evaluation, compliance verification, lending
policy interpretation) to be combined into one transparent recommendation, coordinated through standardized
interfaces rather than ad hoc integration, and operated with the observability, testing, and deployment
discipline a production system needs. The Bootcamp 2 platform has none of that: it coordinates two sub-agents
ad hoc, has no standardized tool protocol, no tracing, no automated tests, and no path to a deployable
artifact. This lab closes that gap for a new, higher-stakes business capability: deciding whether to approve
a loan.
""")

        with st.container(border=True):
            st.markdown("##### Your Role")
            st.markdown("""
You are joining the Enterprise AI Platform Engineering team responsible for operationalizing this multi-agent
platform: you are not just adding a feature, you are making an existing prototype-grade pattern
production-ready.
""")

        with st.container(border=True):
            st.markdown("##### Learning Objectives: by the end of this lab you will be able to")
            lo_col1, lo_col2 = st.columns(2)
            with lo_col1:
                st.markdown("""
- Design a production-ready multi-agent architecture
- Implement a planner-driven orchestration pattern
- Integrate one enterprise tool via the Model Context Protocol
- Monitor a multi-agent workflow with LangSmith
""")
            with lo_col2:
                st.markdown("""
- Validate multi-agent behavior both structurally (in-workflow) and via automated tests
- Containerize an enterprise AI application
- Prepare a platform for enterprise deployment
- Apply the same modular, config-driven engineering discipline established in Bootcamp 1/2 to a production-operations context
""")

        with st.container(border=True):
            st.markdown("##### Dataset: already provided under `data/`")
            ds_col1, ds_col2 = st.columns(2)
            with ds_col1:
                st.markdown("""
**Enterprise Knowledge Base** (`knowledge_base/loans/`)
Reused, unchanged, from Bootcamp 1/2: loan policy documents (auto, home, personal loan guidelines; application process; restructuring/closure), the Lending Policy Agent's RAG source.

**Loan Applications** (`business_data/loan_applications.json`)
5 mock applications (applicant, requested amount, tenure, income, employment status, KYC status).
""")
            with ds_col2:
                st.markdown("""
**Credit Scores** (`business_data/credit_scores.json`)
5 mock credit bureau records (score, delinquencies, credit utilization), keyed by `customer_id`.

**Validation Scenarios** (`validation/test_scenarios.json`)
3 named scenarios used for Activity 2.3's structural validation and to sanity-check Activity 3.1's pytest suite.
""")

    with tab2:
        st.markdown("""
A **single agent** (like Bootcamp 1's) reasons over one job end-to-end. A **coordinator with two routes**
(like Bootcamp 2's) picks one of two sub-agents per turn. This bootcamp introduces a third, more
production-like shape: a **Planner** that decides *what work needs to happen and in what order*, and a
**Coordinator** that *executes that plan* against a fixed roster of specialist agents, aggregating their
outputs into one result.
""")
        components.html(THREE_SHAPES_SVG, height=460)
        st.markdown("""
This "plan, then execute" split matters at production scale for three reasons this lab makes concrete:

- **Separation of concerns.** The Planner's only job is deciding the sequence of work; the Coordinator's only job is running that sequence against real agents. Neither needs to know how the other is implemented, the same reason Bootcamp 2 separated routing (`DecisionEngine`) from execution (`CoordinatorAgent`), one level up.
- **Standardized interfaces.** A production platform can't have every agent talk to every enterprise system in its own bespoke way, it needs a standard protocol. That's what the Model Context Protocol (Activity 2.1) is for: one enterprise capability, wrapped once, callable the same way regardless of which agent (or which future platform) needs it.
- **Operability.** A platform that can't be traced (LangSmith, Activity 2.2), can't validate its own output (`WorkflowValidator`, Activity 2.3), can't be tested automatically (pytest, Activity 3.1), and can't be deployed repeatably (Docker, Activity 3.2) is a prototype, not a production system, regardless of how good its agents' reasoning is.

This lab's Planner pattern is intentionally the simplest illustrative case: one fixed, linear plan (Customer
Profile → Credit Risk → Compliance → Lending Policy → Recommendation), not a dynamic planner that reasons
about which agents to skip or reorders based on intermediate results. That's a deliberate scope decision, not
a missing feature.
""")

    with tab3:
        st.markdown("Here is how this platform is layered, and which folder each layer lives in:")
        components.html(ARCHITECTURE_DIAGRAM_SVG, height=700)
        st.markdown("""
Two things to notice, because you will feel their effect throughout the lab:
- **The notebook (and the Portal) only ever call the Planner and Coordinator.** Every piece of actual reasoning and business logic lives in `src/`, not in the notebook or the UI.
- **Testing, observability, and deployment sit beside the reasoning layers, not above them.** They wrap and check the platform; they don't replace understanding what it actually decided and why.
""")

    import importlib.util
    required_packages = ["openai", "langsmith", "mcp", "faiss", "numpy", "streamlit", "yaml", "dotenv", "pytest"]
    missing_packages = [pkg for pkg in required_packages if importlib.util.find_spec(pkg) is None]

    # OPENAI_API_KEY works with either a real OpenAI key or an OpenRouter
    # key (see .env.example); LLM_BASE_URL picks which one src/llm/ actually
    # talks to.
    key = os.getenv("OPENAI_API_KEY")
    key_missing = not key or key in ("your_openai_api_key_here", "your_openai_or_openrouter_api_key_here")

    required_paths = [
        "config/agent_config.yaml", "config/llm_config.yaml", "config/prompts.yaml", "config/mcp_config.yaml",
        "data/business_data/loan_applications.json", "data/business_data/credit_scores.json",
        "data/validation/test_scenarios.json", "data/knowledge_base/loans",
    ]
    missing_paths = [p for p in required_paths if not (PROJECT_ROOT / p).exists()]

    all_ok = not missing_packages and not key_missing and not missing_paths
    expander_label = "✓ Environment ready" if all_ok else "[WARN] Environment Validation: action needed"

    with st.expander(expander_label, expanded=not all_ok):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Packages**")
            if missing_packages:
                st.error(f"Missing: {', '.join(missing_packages)}\n\nRun: `pip install -r requirements.txt`")
            else:
                st.success("All required packages are installed.")

        with col2:
            st.markdown("**API Key**")
            if key_missing:
                st.error("OPENAI_API_KEY is not set.\n\nCopy `.env.example` to `.env` and add your OpenAI or OpenRouter key.")
            else:
                st.success("OPENAI_API_KEY is configured.")

        with col3:
            st.markdown("**Project Assets**")
            if missing_paths:
                st.error(f"Missing: {', '.join(missing_paths)}")
            else:
                st.success(f"All {len(required_paths)} required project assets are present.")


# ---------------------------------------------------------------------------
# Page: Final Review
# ---------------------------------------------------------------------------

elif selected_page == "Final Review":
    st.markdown("""
    <div class="hero-banner">
        <p class="hero-title">Final Review</p>
        <p class="hero-subtitle">Review everything you've built, then run one final live demonstration</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
Review what you've built across all three phases:
- **Planner-Driven Orchestration**: a `PlannerAgent` builds a fixed 5-step plan; an `AgentCoordinator` executes it against all 5 specialist agents and aggregates their output into one workflow result (Phase 1)
- **Protocol, Observability, and Structural Validation**: one enterprise capability reachable over MCP; a full Planner run traced in LangSmith; the workflow validates its own output shape (Phase 2)
- **Testing and Containerization**: an automated pytest suite; a platform that runs inside Docker (Phase 3)
""")

    if st.button("> Run Final Demo", type="primary"):
        with st.spinner("Running the complete platform end-to-end..."):
            result = run_snippet("""from src.agents.planner_agent import PlannerAgent
from src.core.agent_coordinator import AgentCoordinator
from src.core.workflow_validator import WorkflowValidator
from src.observability.tracing import run_planner_with_tracing

try:
    final_coordinator = AgentCoordinator(planner=PlannerAgent())
    final_validator = WorkflowValidator()

    final_result = run_planner_with_tracing(final_coordinator.run_workflow, "LOAN-5004")
    final_errors = final_validator.validate(final_result)

    print(f"Application: LOAN-5004")
    print(f"Validation errors: {final_errors}")
    print(f"Decision: {final_result.get('recommendation', {}).get('decision')}")
    print(f"Rationale: {final_result.get('recommendation', {}).get('rationale')}")
    print("\\n✓ End-to-end platform execution complete.")
except NotImplementedError as e:
    print(f"[WARN] Not all activities are complete yet: {e}")
""")
        output = (result["stdout"] or "") + (("\n" + result["stderr"]) if result["stderr"] else "")
        st.code(output.strip() or "(no output)", language="text")

    st.markdown("---")
    st.markdown("#### Key Takeaways")

    kt_col1, kt_col2, kt_col3 = st.columns(3)
    with kt_col1:
        st.markdown("""**What You Built**
- A Planner/Coordinator orchestration pattern across five specialist agents
- One enterprise capability exposed via the Model Context Protocol
- A LangSmith-traced orchestration entry point
- Structural, in-workflow output validation
- An automated pytest smoke suite
- A containerized, deployment-documented platform""")
    with kt_col2:
        st.markdown("""**Enterprise/Engineering Principles Applied**
- Separation of concerns between planning and execution
- Standardized protocol integration over ad hoc tool access
- Config-driven, modular implementation (carried forward from Bootcamp 1/2)
- Continuous, runnable validation at every step, never prose alone
- Enterprise readiness as documentation and process, not just code""")
    with kt_col3:
        st.markdown("""**Skills Demonstrated**
- Multi-agent orchestration design (Planner pattern)
- Model Context Protocol server and client implementation
- LLM observability with LangSmith
- Structural validation and automated testing for AI workflows
- Containerization of an AI platform""")

    st.markdown("---")
    st.markdown("""
**Next Steps:** This is the final bootcamp in this series' current arc. From here, consider extending this
platform with the deferred scope this lab intentionally left out: a dynamic/branching planner, custom
LangSmith evaluation datasets, a broader MCP tool surface, or an actual (not just documented) deployment
target.
""")


# ---------------------------------------------------------------------------
# Page: an individual activity
# ---------------------------------------------------------------------------

else:
    activity_id = selected_page.replace("Activity ", "").split(" · ")[0]
    activity = ACTIVITIES_BY_ID[activity_id]

    # Shown once per phase, right before that phase's first activity: the
    # same place the notebook's own phase-intro cell sits, immediately
    # before Activity X.1's cell. Not repeated on X.2/X.3 since you've
    # already seen it by then.
    if activity["id"].endswith(".1"):
        phase_intro = PHASE_INTRO[activity["phase"]]
        st.markdown(f"#### {PHASE_TITLES[activity['phase']]}")
        st.markdown(f"**Objective:** {phase_intro['objective']}")
        st.caption(phase_intro["outcome"])
        st.divider()

    st.markdown(f"""
    <div class="hero-banner">
        <p class="hero-title">Activity {activity['id']} · {activity['title']}</p>
        <p class="hero-subtitle">{activity['module']}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"**What success looks like:** {activity['milestone']}")

    with st.container(border=True):
        st.markdown("#### Business Context")
        st.markdown(activity["business_context"])

    with st.container(border=True):
        st.markdown("#### Objective")
        st.markdown(activity["objective"])

    if activity.get("concept_overview"):
        with st.container(border=True):
            st.markdown("#### Concept Overview")
            st.markdown(activity["concept_overview"])

    with st.container(border=True):
        st.markdown("#### Implementation Instructions")
        st.markdown(activity["instructions"])
        if activity.get("ai_assist"):
            st.info(activity["ai_assist"])

    if activity.get("reference_only_files"):
        # Collapsed by default: a full config file dumped open on the page
        # is exactly the "wall of code" that makes a lab feel harder than it
        # is before anyone's read a word of the instructions above.
        with st.expander(f"Reference Files: {', '.join(activity['reference_only_files'])}"):
            tabs = st.tabs(activity["reference_only_files"])
            for tab, path in zip(tabs, activity["reference_only_files"]):
                with tab:
                    lang = "dockerfile" if "Dockerfile" in path or "docker-compose" in path else "yaml"
                    st.code(read_file(path), language=lang)

    if activity["files"]:
        st.markdown("#### Files to Edit")
        st.info(
            "Open these in VS Code (or your preferred IDE) to write your implementation. This app runs "
            "whatever is currently saved on disk, it doesn't edit files itself."
        )
        target_methods = activity.get("target_methods", {})
        if len(activity["files"]) == 1:
            path = activity["files"][0]
            st.code(path, language="text")
            if path in target_methods:
                render_code_to_work_on(path, target_methods[path])
            render_file_hint(path)
        else:
            # Tab labels already name each file; an extra list above them
            # would just repeat the same names twice in a row.
            tabs = st.tabs(activity["files"])
            for tab, path in zip(tabs, activity["files"]):
                with tab:
                    if path in target_methods:
                        render_code_to_work_on(path, target_methods[path])
                    render_file_hint(path)

    st.divider()
    render_activity_runner(activity)

    st.divider()
    page_index = PAGES.index(selected_page)
    prev_col, next_col = st.columns(2)
    with prev_col:
        if page_index > 0:
            if st.button(f"< {PAGES[page_index - 1]}", use_container_width=True):
                st.session_state.pending_nav = PAGES[page_index - 1]
                st.rerun()
    with next_col:
        if page_index < len(PAGES) - 1:
            if st.button(f"{PAGES[page_index + 1]} >", use_container_width=True, type="primary"):
                st.session_state.pending_nav = PAGES[page_index + 1]
                st.rerun()
