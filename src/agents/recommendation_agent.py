"""
Recommendation Agent - PROVIDED, COMPLETE (vendored-style, per Scope
Decision 1). Participants never edit this file.

The final step of the fixed linear plan (Scope Decision 6): synthesizes the
other four specialist agents' findings (passed in via `context`) into one
Approve/Refer/Decline decision.
"""
import re
from typing import Any, Dict, Optional

from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_DECISION_PATTERN = re.compile(r"Decision:\s*(Approve|Refer|Decline)", re.IGNORECASE)


class RecommendationAgent:
    """Synthesizes customer_profile/credit_risk/compliance/lending_policy
    findings (from `context`) into one final recommendation."""

    def __init__(self, llm_client: Optional[LLMClient] = None, prompt_manager: Optional[PromptManager] = None):
        if llm_client is None:
            # Final synthesis uses config/llm_config.yaml's models.synthesis
            # settings (lower temperature, shorter budget than the other
            # 4 agents' open-ended narration) rather than the default chat
            # settings every other specialist agent uses.
            synthesis_config = load_yaml_config("config/llm_config.yaml").get("models", {}).get("synthesis", {})
            llm_client = LLMClient(
                model=synthesis_config.get("model_name"),
                temperature=synthesis_config.get("temperature"),
                max_tokens=synthesis_config.get("max_tokens"),
            )
        self.llm = llm_client
        self.prompts = prompt_manager or PromptManager()

    def analyze(self, application_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return {"decision": "Approve"|"Refer"|"Decline", "rationale": str}
        synthesized from the prior steps' results in `context`."""
        context = context or {}

        prompt = self.prompts.get_prompt("recommendation_prompt")
        user_message = self.prompts.format_prompt(
            prompt.get("user_template", ""),
            customer_profile_summary=(context.get("customer_profile") or {}).get("summary", "Not available"),
            credit_risk_summary=(
                f"{(context.get('credit_risk') or {}).get('risk_tier', 'Unknown')} - "
                f"{(context.get('credit_risk') or {}).get('summary', 'Not available')}"
            ),
            compliance_summary=(
                f"{(context.get('compliance') or {}).get('status', 'Unknown')} - "
                f"{(context.get('compliance') or {}).get('summary', 'Not available')}"
            ),
            lending_policy_summary=(context.get("lending_policy") or {}).get("summary", "Not available"),
        )
        raw_response = self.llm.generate([
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": user_message},
        ])

        match = _DECISION_PATTERN.search(raw_response or "")
        decision = match.group(1).title() if match else "Refer"

        return {
            "agent": "recommendation",
            "application_id": application_id,
            "decision": decision,
            "rationale": raw_response,
        }
