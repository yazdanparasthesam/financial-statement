"""LLM providers via LangChain — `AI_PROVIDER=gemini|mock`.

MockChatModel is a real LangChain chat model (BaseChatModel) with deterministic
replies keyed off prompt markers, so tests, CI and key-less reviewers exercise the
exact same LangGraph code paths as production Gemini.
"""
import hashlib
import json
import re

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from ...config import Settings


class LLMError(RuntimeError):
    pass


def flatten_messages(messages: list[BaseMessage]) -> str:
    parts = []
    for m in messages:
        c = m.content
        if isinstance(c, str):
            parts.append(c)
        elif isinstance(c, list):  # multimodal parts
            parts.extend(p.get("text", "") for p in c if isinstance(p, dict))
    return "\n".join(parts)


def mock_reply(prompt: str) -> str:
    """Deterministic replies for every prompt family in infra/ai/prompts.py."""
    if "CRITIQUE the following draft" in prompt:
        return json.dumps({"accept": True, "issues": [], "improved_draft": None})
    if "REVISE the following draft" in prompt:
        draft = prompt.split("DRAFT:", 1)[1].strip() if "DRAFT:" in prompt else ""
        return (draft[:400] + "\n\n(revised for tone and figure-consistency per critique — mock)").strip()
    if "Explain this year-over-year anomaly" in prompt:
        pct = re.search(r"Change: (-?[\d.]+)%", prompt)
        section = re.search(r"Section: ([^\n]+)", prompt)
        return (
            f"[MOCK EXPLANATION] The movement in {section.group(1) if section else 'this section'} "
            f"({pct.group(1) if pct else '?'}% year-over-year) most likely reflects a change in "
            "business volume or a one-off event. An auditor would request supporting schedules, "
            "contracts or board minutes. Attach the comparative ledger extract and management's "
            "variance analysis to the filing."
        )
    if "Draft the explanatory note" in prompt:
        section = re.search(r"'([^']+)' section", prompt)
        return (
            f"[MOCK NOTE — {section.group(1) if section else 'general'}] The figures presented in "
            "this section are derived from the company's trial balance for the fiscal year and have "
            "been prepared in accordance with the statutory statement format. All amounts are stated "
            "in the reporting currency. Management is responsible for the preparation and fair "
            "presentation of these statements, including the assessment of going concern."
        )
    if "Suggest a statutory category" in prompt:
        out = []
        for code, name in re.findall(r"^- (\S+) (.+?) \(debit", prompt, flags=re.MULTILINE):
            low = name.lower()
            if any(k in low for k in ("expense", "fee", "cost", "salaries", "salary", "rent", "wage")):
                cat = "operating_expenses"
            elif any(k in low for k in ("revenue", "sales", "income")):
                cat = "revenue"
            elif any(k in low for k in ("suspense", "payable", "loan", "liabilit")):
                cat = "current_liabilities"
            else:
                cat = "current_assets"
            out.append(f"{code}|{cat}|keyword heuristic on account name (mock)")
        return "\n".join(out) or "NO_SUGGESTIONS"
    if "PLAN the audit" in prompt:
        return ("1. #get_statements_summary\n2. #get_validation_report\n"
                "3. #get_anomalies\n4. #get_checklist")
    if "Write the audit memo" in prompt:
        err_fails = len(re.findall(r"\[FAIL\|error", prompt))
        warn_fails = len(re.findall(r"\[FAIL\|warning", prompt))
        obs = len(re.findall(r"^\[\w+\] ", prompt, flags=re.MULTILINE))
        if err_fails:
            gate = f"BLOCKED — {err_fails} failing error-rule(s) must be resolved before submission."
        elif warn_fails:
            gate = (f"PASS WITH WARNINGS — {warn_fails} warning finding(s) (e.g. anomalies) "
                    "do not block submission but need explanations.")
        else:
            gate = "CLEAR — no failing rules; the submission gate can pass."
        return (
            f"[MOCK AUDIT MEMO] ReWOO audit synthesized from {obs} tool observations.\n"
            f"Gate status: {gate}\n"
            "All figures quoted by the deterministic engine; no numbers were computed by the model.\n"
            "Recommendation: attach variance explanations for flagged anomalies and re-run "
            "validation after any change."
        )
    return ("[MOCK ASSISTANT] I can help with this filing's statements, ratios, cash flow, "
            "validations and notes. Live tool-using answers require AI_PROVIDER=gemini with "
            "GEMINI_API_KEY set; in mock mode I return deterministic guidance so the ReAct "
            "workflow stays testable offline.")


class MockChatModel(BaseChatModel):
    """Deterministic offline chat model — same LangChain contract as any provider."""

    model_label: str = "mock-deterministic-v2"

    @property
    def _llm_type(self) -> str:
        return "fs-mock"

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None,
                  run_manager=None, **kwargs) -> ChatResult:
        reply = mock_reply(flatten_messages(messages))
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply))])

    def bind_tools(self, tools, **kwargs):
        return self


def get_chat_model(settings: Settings):
    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError as e:  # pragma: no cover
            raise LLMError("langchain-google-genai is not installed") from e
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
            temperature=0.2,
            max_output_tokens=1500,
        )
    return MockChatModel()


def provider_name(llm) -> str:
    return "gemini" if type(llm).__name__ == "ChatGoogleGenerativeAI" else "mock"


def model_name(llm, settings: Settings) -> str:
    return settings.gemini_model if provider_name(llm) == "gemini" else getattr(llm, "model_label", "mock")


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def parse_mapping_suggestions(text: str) -> list[dict]:
    """Parse 'CODE|CATEGORY|reason' lines from the mapping-suggest response."""
    out = []
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            out.append({"code": parts[0], "suggested_category": parts[1],
                        "reason": parts[2] if len(parts) > 2 else ""})
    return out
