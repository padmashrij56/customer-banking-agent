"""
Compliance Agent - PROVIDED, COMPLETE (vendored-style, per Scope Decision 1).
Participants never edit this file.
"""
from typing import Any, Dict, List, Optional

from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.services.loan_application_service import get_loan_application
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ComplianceAgent:
    """Runs a small set of regulatory/policy checks (KYC status, loan-to-
    income multiple) and narrates the result via the LLM."""

    def __init__(self, llm_client: Optional[LLMClient] = None, prompt_manager: Optional[PromptManager] = None):
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_manager or PromptManager()
        config = load_yaml_config("config/agent_config.yaml")
        self.rules = config.get("compliance", {})

    def analyze(self, application_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a Pass/Flagged compliance status and narrative for the
        given application."""
        application = get_loan_application(application_id)
        if "error" in application:
            return {"agent": "compliance", "error": application["error"], "application_id": application_id}

        flags: List[str] = []

        required_kyc = self.rules.get("required_kyc_status", "Verified")
        if application.get("kyc_status") != required_kyc:
            flags.append(f"KYC status is '{application.get('kyc_status')}', expected '{required_kyc}'")

        annual_income = application.get("annual_income") or 1
        requested_amount = application.get("requested_amount", 0)
        loan_to_income_multiple = round(requested_amount / annual_income, 2)
        max_multiple = self.rules.get("max_loan_to_income_multiple", 10)
        if loan_to_income_multiple > max_multiple:
            flags.append(
                f"Loan-to-income multiple {loan_to_income_multiple}x exceeds policy max {max_multiple}x"
            )

        status = "Flagged" if flags else "Pass"

        prompt = self.prompts.get_prompt("compliance_prompt")
        user_message = self.prompts.format_prompt(
            prompt.get("user_template", ""),
            kyc_status=application.get("kyc_status"),
            loan_to_income_multiple=loan_to_income_multiple,
            max_multiple=max_multiple,
            flags="; ".join(flags) if flags else "None",
        )
        narrative = self.llm.generate([
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": user_message},
        ])

        return {
            "agent": "compliance",
            "application_id": application_id,
            "status": status,
            "flags": flags,
            "summary": narrative,
        }
