"""
Lending Policy Agent - PROVIDED, COMPLETE (vendored-style, per Scope
Decision 1). Participants never edit this file.

Uses the reused FAISS knowledge base (src/knowledge/*, data/knowledge_base/loans/,
carried forward unchanged from Bootcamp 1/2) for RAG-based policy
interpretation.
"""
from typing import Any, Dict, Optional

from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.retriever import Retriever
from src.llm.llm_client import LLMClient
from src.llm.prompt_manager import PromptManager
from src.services.loan_application_service import get_loan_application
from src.utils.config_loader import load_yaml_config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LendingPolicyAgent:
    """Interprets bank lending policy for an application via RAG retrieval
    over data/knowledge_base/loans/."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        prompt_manager: Optional[PromptManager] = None,
        knowledge_base: Optional[KnowledgeBase] = None,
    ):
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_manager or PromptManager()
        config = load_yaml_config("config/agent_config.yaml")
        self.settings = config.get("lending_policy", {})

        self.kb = knowledge_base or KnowledgeBase()
        self._index_built = False

    def _ensure_index(self):
        """Build the FAISS index over the loan policy documents on first use
        (lazy - avoids an embedding API call at construction time)."""
        if self._index_built:
            return
        docs = self.kb.load_documents(self.settings.get("knowledge_base_path", "data/knowledge_base/loans"))
        self.kb.build_index(docs)
        self._index_built = True

    def analyze(self, application_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a policy interpretation and citations for the given
        application."""
        application = get_loan_application(application_id)
        if "error" in application:
            return {"agent": "lending_policy", "error": application["error"], "application_id": application_id}

        self._ensure_index()
        retriever = Retriever(self.kb)
        query = f"{application.get('loan_type')} loan policy for amount {application.get('requested_amount')}"
        results = retriever.retrieve(
            query,
            top_k=self.settings.get("top_k", 4),
            threshold=self.settings.get("similarity_threshold", 0.5),
        )

        policy_excerpts = "\n\n".join(r["content"] for r in results) or "No matching policy excerpts found."
        citations = [{"source": r["source"], "category": r["category"], "score": r["score"]} for r in results]

        prompt = self.prompts.get_prompt("lending_policy_prompt")
        user_message = self.prompts.format_prompt(
            prompt.get("user_template", ""),
            loan_type=application.get("loan_type"),
            requested_amount=application.get("requested_amount"),
            tenure_months=application.get("tenure_months"),
            policy_excerpts=policy_excerpts,
        )
        summary = self.llm.generate([
            {"role": "system", "content": prompt.get("system", "")},
            {"role": "user", "content": user_message},
        ])

        return {
            "agent": "lending_policy",
            "application_id": application_id,
            "summary": summary,
            "citations": citations,
        }
