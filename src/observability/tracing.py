"""
LangSmith Observability.

TODO: Participants will implement run_planner_with_tracing() (Activity 2.2)
- the one orchestration entry point wrapped in tracing (Scope Decision 3:
two env vars plus one traced entry point, no dashboards/eval datasets).
configure_langsmith()'s env loading and _run_with_local_trace()'s
stdout fallback trace below are both prefilled.
"""
import os
import time
from typing import Any, Callable

from dotenv import load_dotenv

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def configure_langsmith() -> bool:
    """Read the two LangSmith env vars and report whether tracing is
    enabled. Prefilled - do not edit.

    Reads LANGCHAIN_TRACING_V2 and LANGCHAIN_API_KEY from the environment
    (via .env - see .env.example). Returns True only when tracing is turned
    on AND a (non-placeholder) API key is present; otherwise returns False
    so the workflow still runs untraced rather than failing.
    """
    load_dotenv()
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "false").strip().lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    has_key = bool(api_key) and "your_langsmith_api_key_here" not in api_key

    if tracing_flag and not has_key:
        logger.warning("LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY is missing/placeholder - tracing disabled.")
        return False

    os.environ.setdefault("LANGCHAIN_PROJECT", "loan-underwriting-platform")
    return tracing_flag and has_key


# --- Prefilled: local fallback trace -----------------------------------------
# When LangSmith is not configured, there is still value in *seeing* what the
# run did. This prints a compact, ordered, one-line-per-step summary of the
# workflow to stdout, so Activity 2.2 always produces a visible trace artifact
# - with or without a LangSmith account. Do not edit; your job is the
# tracing branch in run_planner_with_tracing() below.
_SECTION_FIELDS = {
    "customer_profile": ("employment_status", "annual_income"),
    "credit_risk": ("credit_score", "debt_to_income_pct", "risk_tier"),
    "compliance": ("status", "flags"),
    "lending_policy": ("citations",),
    "recommendation": ("decision",),
}


def _summarize_section(name: str, section: Any) -> str:
    if not isinstance(section, dict):
        return repr(section)
    if "error" in section:
        return f"error: {section['error']}"
    parts = []
    for key in _SECTION_FIELDS.get(name, ()):
        if key not in section:
            continue
        value = section[key]
        if key == "flags" and isinstance(value, list):
            value = len(value)
        if key == "citations" and isinstance(value, list):
            value = f"{len(value)} sources"
        parts.append(f"{key}={value}")
    if parts:
        return "  ".join(parts)
    return ", ".join(k for k in section if k not in ("agent", "application_id", "summary", "rationale"))


def _run_with_local_trace(run_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Run `run_fn` untraced, printing an ordered step summary to stdout.
    Prefilled - do not edit."""
    bar = "-" * 62
    print(bar)
    print(" Local run trace   (LangSmith not configured)")
    print(" set LANGCHAIN_TRACING_V2=true + a real LANGCHAIN_API_KEY in .env")
    print(" for a full trace at https://smith.langchain.com")
    print(bar)

    started = time.perf_counter()
    result = run_fn(*args, **kwargs)
    elapsed = time.perf_counter() - started

    if isinstance(result, dict) and result and all(isinstance(v, dict) for v in result.values()):
        for i, (name, section) in enumerate(result.items(), start=1):
            print(f"  {i}. {name:<18} {_summarize_section(name, section)}")
        print(bar)
        print(f"  {len(result)} steps in {elapsed:.2f}s")
    else:
        print(f"  run completed in {elapsed:.2f}s")
    print(bar)
    return result
# ---------------------------------------------------------------------------


def run_planner_with_tracing(run_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    Run `run_fn(*args, **kwargs)` (e.g. an AgentCoordinator.run_workflow
    bound method) wrapped in LangSmith tracing when tracing is enabled.

    TODO (Activity 2.2):
    1. Call `tracing_enabled = configure_langsmith()`.
    2. If tracing_enabled is False, call and return
       `_run_with_local_trace(run_fn, *args, **kwargs)` - the prefilled
       helper above. It runs the workflow untraced but prints an ordered
       local trace, so the run is always visible. Never raise or block on a
       missing/disabled LangSmith configuration.
    3. If tracing_enabled is True, import `traceable` from `langsmith`
       (`from langsmith import traceable`), wrap run_fn with it - e.g.
       `traced_fn = traceable(name="loan_underwriting_planner_run")(run_fn)` -
       and call/return `traced_fn(*args, **kwargs)`.
    """
    # TODO: check configure_langsmith(), then either call
    # _run_with_local_trace(run_fn, *args, **kwargs) or wrap run_fn with
    # langsmith.traceable() first.
    tracing_enabled = configure_langsmith()
    if not tracing_enabled:
        return _run_with_local_trace(run_fn, *args, **kwargs)

    from langsmith import traceable

    traced_fn = traceable(name="loan_underwriting_planner_run")(run_fn)
    return traced_fn(*args, **kwargs)
    # raise NotImplementedError("run_planner_with_tracing is not implemented yet - see src/observability/tracing.py")
