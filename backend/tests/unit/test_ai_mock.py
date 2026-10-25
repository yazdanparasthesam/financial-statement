"""Unit tests for the AI layer: LangChain providers + the three LangGraph agent
patterns (self-criticism, ReAct, ReWOO) — fully offline via MockChatModel."""
import json

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.config import Settings
from app.infra.ai import graphs, prompts
from app.infra.ai.providers import (
    MockChatModel,
    get_chat_model,
    mock_reply,
    parse_mapping_suggestions,
    prompt_hash,
    provider_name,
)


class StrictCritic(BaseChatModel):
    """Test double: rejects the first `rejects` critiques, then accepts.
    All other steps fall through to the deterministic mock replies."""

    rejects: int = 2
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "strict-critic-test"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        text = "\n".join(m.content if isinstance(m.content, str) else "" for m in messages)
        if "CRITIQUE the following draft" in text:
            self.calls += 1
            payload = ({"accept": False, "issues": ["tone too informal"], "improved_draft": None}
                       if self.calls <= self.rejects
                       else {"accept": True, "issues": [], "improved_draft": None})
            content = json.dumps(payload)
        else:
            content = mock_reply(text)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])


# ---------------------------------------------------------------- providers

@pytest.mark.unit
def test_mock_reply_markers_are_deterministic():
    a = {"account_code": "pl:revenue", "account_name": "Revenue", "prior_value": 260000.0,
         "current_value": 440000.0, "pct_change": 69.2}
    s, u = prompts.anomaly_explain(a, "ctx")
    r1, r2 = mock_reply(s + "\n" + u), mock_reply(s + "\n" + u)
    assert r1 == r2 and "MOCK EXPLANATION" in r1 and "69.2%" in r1

    s, u = prompts.notes_draft("revenue", "ctx", "vals")
    assert "MOCK NOTE — revenue" in mock_reply(s + "\n" + u)

    s, u = prompts.mapping_suggest([{"code": "9999", "name": "Mystery Fee",
                                     "debit": 5.0, "credit": 0.0}])
    line = mock_reply(s + "\n" + u).splitlines()[0]
    assert line.startswith("9999|operating_expenses|")


@pytest.mark.unit
def test_mock_reply_agent_pattern_markers():
    s, u = prompts.critique("revenue", "some draft")
    crit = json.loads(mock_reply(s + "\n" + u))
    assert crit["accept"] is True and crit["issues"] == []

    s, u = prompts.revise("revenue", "DRAFTBODY", ["too informal"])
    assert "revised for tone" in mock_reply(s + "\n" + u)

    s, u = prompts.rewoo_plan("ctx", ["get_checklist", "get_validation_report"])
    plan = mock_reply(s + "\n" + u)
    assert "#get_statements_summary" in plan and "#get_checklist" in plan

    s, u = prompts.rewoo_solve("ctx", ["get_validation_report"],
                               ["[get_validation_report] [FAIL|warning|R006] anomalies"])
    memo = mock_reply(s + "\n" + u)
    assert "MOCK AUDIT MEMO" in memo and "PASS WITH WARNINGS" in memo

    assert "MOCK ASSISTANT" in mock_reply("random question")


@pytest.mark.unit
def test_mock_solver_gate_wording():
    s, u = prompts.rewoo_solve("ctx", ["t"], ["[t] [FAIL|error|R002] identity broken"])
    assert "BLOCKED" in mock_reply(s + "\n" + u)
    s, u = prompts.rewoo_solve("ctx", ["t"], ["[t] [PASS|error|R002] ok"])
    assert "CLEAR" in mock_reply(s + "\n" + u)


@pytest.mark.unit
def test_chat_model_and_provider_selection():
    llm = MockChatModel()
    out = llm.invoke([HumanMessage(content="hello")])
    assert "MOCK ASSISTANT" in out.content
    assert llm.bind_tools([]) is llm  # ReAct compatibility shim
    assert provider_name(llm) == "mock"
    # gemini without key falls back to mock (never crashes key-less reviewers)
    assert isinstance(get_chat_model(Settings(ai_provider="gemini", gemini_api_key="")), MockChatModel)
    assert isinstance(get_chat_model(Settings(ai_provider="mock")), MockChatModel)


@pytest.mark.unit
def test_prompt_hash_and_mapping_parse():
    assert prompt_hash("ab") == prompt_hash("ab") != prompt_hash("ac")
    assert len(prompt_hash("ab")) == 16
    out = parse_mapping_suggestions(
        "9999|operating_expenses|name contains 'Fee'\n9998|current_liabilities|suspense\nBADLINE")
    assert len(out) == 2
    assert out[0] == {"code": "9999", "suggested_category": "operating_expenses",
                      "reason": "name contains 'Fee'"}


# ---------------------------------------------------------------- self-criticism graph

@pytest.mark.unit
def test_notes_graph_accepts_first_draft():
    graph = graphs.build_notes_graph(MockChatModel(), max_loops=2)
    out = graph.invoke(graphs.notes_initial_state("revenue", "ctx", "vals"))
    assert "MOCK NOTE — revenue" in out["final"]
    assert [s["step"] for s in out["trace"]] == ["draft", "critique"]
    assert out["loops"] == 0


@pytest.mark.unit
def test_notes_graph_revises_until_accept():
    graph = graphs.build_notes_graph(StrictCritic(rejects=2), max_loops=5)
    out = graph.invoke(graphs.notes_initial_state("revenue", "ctx", "vals"))
    steps = [s["step"] for s in out["trace"]]
    assert steps.count("revise") == 2 and steps[-1] == "critique"
    assert "revised for tone" in out["final"] and out["loops"] == 2


@pytest.mark.unit
def test_notes_graph_loop_is_bounded():
    graph = graphs.build_notes_graph(StrictCritic(rejects=99), max_loops=2)
    out = graph.invoke(graphs.notes_initial_state("equity", "ctx", "vals"))
    assert out["loops"] == 2  # never runs away
    assert [s["step"] for s in out["trace"]].count("revise") == 2
    assert out["final"]


@pytest.mark.unit
def test_parse_critique_robust():
    assert graphs.parse_critique('{"accept": false, "issues": ["x"]}')["accept"] is False
    bad = graphs.parse_critique("not json at all")
    assert bad["accept"] is True and bad["issues"]  # unparsable -> accept with a note


# ---------------------------------------------------------------- ReWOO graph

@pytest.mark.unit
def test_audit_graph_full_run():
    registry = {
        "get_statements_summary": lambda: "P&L: net profit 60,000",
        "get_validation_report": lambda: "[PASS|error|R001] balanced\n[FAIL|warning|R006] anomalies",
        "get_anomalies": lambda: "pl:revenue +69.2%",
        "get_checklist": lambda: "Checklist 5/8 done",
        "get_deadline": lambda: "deadline in 200 days",
        "get_ratios": lambda: "current ratio 4.6429",
    }
    graph = graphs.build_audit_graph(MockChatModel(), registry)
    out = graph.invoke(graphs.audit_initial_state("company X FY2026"))
    assert out["plan"] == ["get_statements_summary", "get_validation_report",
                           "get_anomalies", "get_checklist"]
    assert len(out["observations"]) == 4
    assert all(o.startswith(f"[{n}]") for n, o in zip(out["plan"], out["observations"], strict=True))
    assert "MOCK AUDIT MEMO" in out["memo"] and "PASS WITH WARNINGS" in out["memo"]


@pytest.mark.unit
def test_audit_graph_filters_unknown_tools():
    registry = {"get_checklist": lambda: "3/8 done"}
    graph = graphs.build_audit_graph(MockChatModel(), registry)
    out = graph.invoke(graphs.audit_initial_state("ctx"))
    assert out["plan"] == ["get_checklist"]  # planned-but-missing tools are dropped
    assert out["observations"] == ["[get_checklist] 3/8 done"]


@pytest.mark.unit
def test_audit_graph_tool_error_is_observation():
    def boom():
        raise RuntimeError("db down")
    graph = graphs.build_audit_graph(MockChatModel(), {"get_checklist": boom})
    out = graph.invoke(graphs.audit_initial_state("ctx"))
    assert "tool error" in out["observations"][0] and out["memo"]


# ---------------------------------------------------------------- ReAct agent

@pytest.mark.unit
def test_react_agent_answers_without_tools_in_mock_mode():
    from langchain_core.tools import StructuredTool
    tools = [StructuredTool.from_function(func=lambda: "net profit 60,000",
                                          name="get_statements_summary", description="summary")]
    agent = graphs.build_assistant_agent(MockChatModel(), tools, prompts.ASSISTANT_SYSTEM)
    out = agent.invoke({"messages": [HumanMessage(content="What is the net profit?")]})
    assert "MOCK ASSISTANT" in out["messages"][-1].content


@pytest.mark.unit
def test_parse_plan():
    assert graphs.parse_plan("1. #a\n2. #b_tool\nprose #ignored- dash") == ["a", "b_tool"]
