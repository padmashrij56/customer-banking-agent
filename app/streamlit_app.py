"""
Enterprise Loan Underwriting Portal - Streamlit UI.
Complete implementation, provided for immediate use (presentation layer -
participants are not asked to build UI, per the spec's "lightweight
application simulator" principle).
"""
import json
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

st.set_page_config(
    page_title="Enterprise Loan Underwriting Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {font-size: 2.4rem; color: #1f4788; font-weight: bold;}
    .sub-header {font-size: 1.1rem; color: #555; margin-bottom: 1.5rem;}
    .section-card {background-color: #f5f5f5; border-left: 4px solid #4caf50; padding: 1rem; border-radius: 0.4rem; margin-bottom: 1rem;}
    .decision-approve {background-color: #e8f5e9; border-left: 4px solid #2e7d32; padding: 1rem; border-radius: 0.4rem;}
    .decision-refer {background-color: #fff3e0; border-left: 4px solid #e65100; padding: 1rem; border-radius: 0.4rem;}
    .decision-decline {background-color: #ffebee; border-left: 4px solid #c62828; padding: 1rem; border-radius: 0.4rem;}
    .stButton>button {background-color: #1f4788; color: white; font-weight: bold;}
</style>
""",
    unsafe_allow_html=True,
)

if "coordinator_initialized" not in st.session_state:
    st.session_state.coordinator_initialized = False


def initialize_platform():
    """Initialize the real AgentCoordinator, wiring the whole platform
    together (Planner + 5 specialist agents + WorkflowValidator)."""
    try:
        from src.core.agent_coordinator import AgentCoordinator
        from src.core.workflow_validator import WorkflowValidator

        st.session_state.coordinator = AgentCoordinator()
        st.session_state.validator = WorkflowValidator()
        st.session_state.coordinator_initialized = True
        return True
    except NotImplementedError as e:
        st.session_state.coordinator_initialized = False
        st.session_state.init_error = str(e)
        return False
    except Exception as e:  # pragma: no cover - surfaced directly to the UI
        logger.error(f"Platform initialization failed: {e}")
        st.session_state.coordinator_initialized = False
        st.session_state.init_error = str(e)
        return False


def load_applications():
    path = Path("data/business_data/loan_applications.json")
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("applications", [])


st.markdown('<div class="main-header">🏦 Enterprise Loan Underwriting Portal</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Planner-orchestrated multi-agent underwriting - '
    "Customer Profile · Credit Risk · Compliance · Lending Policy · Recommendation</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Platform Status")
    if not st.session_state.coordinator_initialized:
        if st.button("Initialize Platform", type="primary"):
            with st.spinner("Wiring Planner, Coordinator, and specialist agents..."):
                if initialize_platform():
                    st.success("Platform initialized.")
                    st.rerun()
    else:
        st.success("Platform ready.")

    if not st.session_state.coordinator_initialized and st.session_state.get("init_error"):
        st.info(
            "Not implemented yet: "
            f"{st.session_state.init_error}\n\nComplete the guided workbook's activities, "
            "then click Initialize Platform again."
        )

    st.divider()
    st.caption("Enterprise Loan Underwriting Platform · Bootcamp 3")

applications = load_applications()
application_ids = [a["application_id"] for a in applications]

st.subheader("Run Underwriting Workflow")
selected_id = st.selectbox("Loan application", application_ids) if application_ids else None

if st.button("Run Workflow", disabled=not st.session_state.coordinator_initialized or not selected_id):
    with st.spinner(f"Running the underwriting workflow for {selected_id}..."):
        try:
            result = st.session_state.coordinator.run_workflow(selected_id)
            errors = st.session_state.validator.validate(result)
            st.session_state.last_result = result
            st.session_state.last_errors = errors
        except NotImplementedError as e:
            st.warning(f"Not implemented yet: {e}")
        except Exception as e:
            logger.error(f"Workflow run failed: {e}")
            st.error(f"Workflow run failed: {e}")

if st.session_state.get("last_result"):
    result = st.session_state.last_result
    errors = st.session_state.get("last_errors")

    if errors:
        st.error("Workflow output failed validation: " + "; ".join(errors))

    recommendation = result.get("recommendation", {})
    decision = recommendation.get("decision", "Unknown")
    decision_class = {
        "Approve": "decision-approve",
        "Refer": "decision-refer",
        "Decline": "decision-decline",
    }.get(decision, "section-card")

    st.markdown(
        f'<div class="{decision_class}"><strong>Decision: {decision}</strong><br>{recommendation.get("rationale", "")}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    labels = [
        ("customer_profile", "Customer Profile"),
        ("credit_risk", "Credit Risk"),
        ("compliance", "Compliance"),
        ("lending_policy", "Lending Policy"),
    ]
    for col, (key, label) in zip(cols, labels):
        with col:
            section = result.get(key, {})
            st.markdown(f"**{label}**")
            st.markdown(
                f'<div class="section-card">{section.get("summary", "No summary available.")}</div>',
                unsafe_allow_html=True,
            )
else:
    st.info("Initialize the platform, select an application, and click Run Workflow.")
