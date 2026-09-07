"""
Credit Risk Agent - PROVIDED, COMPLETE (vendored-style, per Scope Decision 1).
Participants never edit this file.
"""
from typing import Any, Dict, Optional

from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.services.loan_application_service import get_loan_application
from src.services.credit_score_service import get_credit_score
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CreditRiskAgent:
    """Computes a risk tier from bureau data and application figures, and
    narrates it via the LLM."""

    def __init__(self, llm_client: Optional[LLMClient] = None, prompt_manager: Optional[PromptManager] = None):
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_manager or PromptManager()
        config = load_yaml_config("config/agent_config.yaml")
        self.thresholds = config.get("credit_risk", {})

    def _risk_tier(self, credit_score: int, debt_to_income_pct: float) -> str:
        low_min = self.thresholds.get("score_thresholds", {}).get("low_risk_min", 750)
        med_min = self.thresholds.get("score_thresholds", {}).get("medium_risk_min", 650)
        max_dti = self.thresholds.get("max_debt_to_income_pct", 45)

        if credit_score >= low_min and debt_to_income_pct <= max_dti:
            return "Low"
        if credit_score >= med_min:
            return "Medium"
        return "High"

    def analyze(self, application_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a risk tier and narrative for the given application."""
        application = get_loan_application(application_id)
        if "error" in application:
            return {"agent": "credit_risk", "error": application["error"], "application_id": application_id}

        credit = get_credit_score(application.get("customer_id"))
        if "error" in credit:
            return {"agent": "credit_risk", "error": credit["error"], "application_id": application_id}

        annual_income = application.get("annual_income") or 1
        existing_emis = application.get("existing_emis", 0)
        debt_to_income_pct = round((existing_emis * 12) / annual_income * 100, 2)
        risk_tier = self._risk_tier(credit.get("credit_score", 0), debt_to_income_pct)

        prompt = self.prompts.get_prompt("credit_risk_prompt")
        user_message = self.prompts.format_prompt(
            prompt.get("user_template", ""),
            credit_score=credit.get("credit_score"),
            debt_to_income_pct=debt_to_income_pct,
            risk_tier=risk_tier,
            delinquencies=credit.get("delinquencies"),
        )
        narrative = self.llm.generate([
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": user_message},
        ])

        return {
            "agent": "credit_risk",
            "application_id": application_id,
            "credit_score": credit.get("credit_score"),
            "debt_to_income_pct": debt_to_income_pct,
            "risk_tier": risk_tier,
            "summary": narrative,
        }
