"""LangSmith Observability - REFERENCE SOLUTION"""
import os
import time
from typing import Any, Callable

from dotenv import load_dotenv

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def configure_langsmith() -> bool:
    load_dotenv()
    tracing_flag = os.getenv("LANGCHAIN_TRACING_V2", "false").strip().lower() == "true"
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    has_key = bool(api_key) and "your_langsmith_api_key_here" not in api_key

    if tracing_flag and not has_key:
        logger.warning("LANGCHAIN_TRACING_V2=true but LANGCHAIN_API_KEY is missing/placeholder - tracing disabled.")
        return False

    os.environ.setdefault("LANGCHAIN_PROJECT", "loan-underwriting-platform")
    return tracing_flag and has_key


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


def run_planner_with_tracing(run_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    tracing_enabled = configure_langsmith()
    if not tracing_enabled:
        return _run_with_local_trace(run_fn, *args, **kwargs)

    from langsmith import traceable

    traced_fn = traceable(name="loan_underwriting_planner_run")(run_fn)
    return traced_fn(*args, **kwargs)
