"""
Customer Profile Agent - PROVIDED, COMPLETE (vendored-style, per Scope
Decision 1). Participants never edit this file; Activity 1.3's job is
wiring it (and its 4 sibling agents) into the Planner's executable steps via
src/core/agent_coordinator.py, not writing any agent's internal reasoning.
"""
from typing import Any, Dict, Optional

from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.services.loan_application_service import get_loan_application
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CustomerProfileAgent:
    """Analyzes an applicant's financial profile and employment stability."""

    def __init__(self, llm_client: Optional[LLMClient] = None, prompt_manager: Optional[PromptManager] = None):
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_manager or PromptManager()

    def analyze(self, application_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a customer-profile summary for the given application."""
        application = get_loan_application(application_id)
        if "error" in application:
            return {"agent": "customer_profile", "error": application["error"], "application_id": application_id}

        prompt = self.prompts.get_prompt("customer_profile_prompt")
        user_message = self.prompts.format_prompt(
            prompt.get("user_template", ""),
            applicant_name=application.get("applicant_name"),
            employment_status=application.get("employment_status"),
            annual_income=application.get("annual_income"),
            existing_emis=application.get("existing_emis"),
            loan_type=application.get("loan_type"),
            requested_amount=application.get("requested_amount"),
        )
        summary = self.llm.generate([
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": user_message},
        ])

        return {
            "agent": "customer_profile",
            "application_id": application_id,
            "applicant_name": application.get("applicant_name"),
            "employment_status": application.get("employment_status"),
            "annual_income": application.get("annual_income"),
            "summary": summary,
        }
