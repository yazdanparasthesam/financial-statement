# Agent Capabilities

Reusable, documented capabilities an agent can pick up when working with Financial Statement —
the "what a specialist can do here" layer of the extension pack.

| Capability | File | Uses |
|---|---|---|
| Filing audit workflow | `workflows/filing-audit.md` | MCP server (read-only) |
| Anomaly explanation | `prompts/anomaly-explain.md` | runtime + agent reuse |
| Notes drafting | `prompts/notes-draft.md` | runtime + agent reuse |
| Mapping suggestion | `prompts/mapping-suggest.md` | runtime + agent reuse |
| Review summary | `prompts/review-summary.md` | reviewer-side agents |
| Self-critique notes loop | `prompts/self-critique-notes.md` | runtime (LangGraph) + agent reuse |
| ReAct assistant | `prompts/react-assistant.md` | runtime (LangGraph) + agent reuse |
| ReWOO audit memo | `prompts/rewoo-audit-memo.md` | runtime (LangGraph) + agent reuse |

The `prompts/*.md` files mirror `backend/app/infra/ai/prompts.py` (single source of truth
in code; these are the human/agent-readable copies with usage notes). If they drift, the
code wins — and docs/ai-workflow.md must record the change.
