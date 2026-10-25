"""Prompt library — single source of truth, mirrored in agent-capabilities/prompts/."""

SYSTEM_BASE = (
    "You are the Financial Statement assistant for Iranian statutory financial statements and tax filings "
    "(English output). HARD RULES: never compute or invent numbers — only use the figures "
    "given to you; never ask for or echo credentials, national IDs, or economic codes; "
    "be concise, professional, auditor-friendly. If data is insufficient, say so."
)


def anomaly_explain(anomaly: dict, statements_summary: str) -> tuple[str, str]:
    user = (
        f"Explain this year-over-year anomaly for the notes to the accounts.\n"
        f"Section: {anomaly['account_name']} ({anomaly['account_code']})\n"
        f"Prior year: {anomaly['prior_value']:,.2f}\n"
        f"Current year: {anomaly['current_value']:,.2f}\n"
        f"Change: {anomaly['pct_change']}%\n"
        f"Statement context:\n{statements_summary}\n"
        "Write 2-4 sentences: most likely business drivers, what an auditor would ask, "
        "and what supporting evidence the preparer should attach."
    )
    return SYSTEM_BASE, user


def notes_draft(section: str, statements_summary: str, validations_summary: str) -> tuple[str, str]:
    user = (
        f"Draft the explanatory note for the '{section}' section of the financial statements.\n"
        f"Statement figures:\n{statements_summary}\n"
        f"Validation findings:\n{validations_summary}\n"
        "Write a formal note (one paragraph, up to 120 words) suitable for inclusion in "
        "the notes to the accounts. Use ONLY the figures provided."
    )
    return SYSTEM_BASE, user


def mapping_suggest(unmapped: list[dict]) -> tuple[str, str]:
    lines = "\n".join(f"- {a['code']} {a['name']} (debit {a['debit']:,.2f}, credit {a['credit']:,.2f})"
                      for a in unmapped[:25])
    user = (
        "Suggest a statutory category for each unmapped trial-balance account.\n"
        "Allowed categories: current_assets, non_current_assets, current_liabilities, "
        "non_current_liabilities, equity, revenue, cogs, operating_expenses, other_income, "
        "other_expenses, tax_expense.\n"
        f"Accounts:\n{lines}\n"
        "Reply with exactly one line per account: CODE|CATEGORY|short reason"
    )
    return SYSTEM_BASE, user


ASSISTANT_SYSTEM = SYSTEM_BASE + (
    " You are a ReAct agent: reason step by step and CALL THE TOOLS to fetch facts before "
    "answering. Never answer a numeric question from memory — use a tool, quote its output."
)


def chat(message: str, filing_context: str) -> tuple[str, str]:
    system = ASSISTANT_SYSTEM + f"\n\nFiling context (already fetched, use as needed):\n{filing_context}"
    return system, message


# ---------- self-criticism (reflection) loop prompts ----------

def critique(section: str, draft: str) -> tuple[str, str]:
    system = SYSTEM_BASE + (
        " You are the CRITIC in a self-criticism loop over a financial-statement note. "
        "Judge only the draft given to you."
    )
    user = (
        f"CRITIQUE the following draft note for the '{section}' section.\n"
        "Criteria: (1) every figure in the draft appears in the provided statements context; "
        "(2) formal, auditor-friendly tone; (3) at most 120 words; (4) no invented facts.\n"
        f"DRAFT:\n{draft}\n\n"
        'Reply with STRICT JSON only: {"accept": true|false, "issues": ["..."], '
        '"improved_draft": "..." or null}. Set accept=true only if all criteria hold.'
    )
    return system, user


def revise(section: str, draft: str, issues: list[str]) -> tuple[str, str]:
    system = SYSTEM_BASE + " You are the REVISER in a self-criticism loop."
    user = (
        f"REVISE the following draft note for the '{section}' section, fixing every issue.\n"
        f"ISSUES:\n" + "\n".join(f"- {i}" for i in issues) +
        f"\n\nDRAFT:\n{draft}\n\nReturn ONLY the revised note text (no preamble)."
    )
    return system, user


# ---------- ReWOO (plan → execute → solve) prompts ----------

def rewoo_plan(context: str, tool_names: list[str]) -> tuple[str, str]:
    system = SYSTEM_BASE + (
        " You are the PLANNER of a ReWOO audit: produce the full tool plan up front, "
        "without seeing observations."
    )
    user = (
        "PLAN the audit of this filing using ONLY the tools below. One tool per line, "
        "strict format 'N. #tool_name'. Use each tool at most once; order matters.\n"
        f"TOOLS: {', '.join('#' + n for n in tool_names)}\n\n"
        f"FILING CONTEXT:\n{context}\n\nPLAN:"
    )
    return system, user


def rewoo_solve(context: str, plan: list[str], observations: list[str]) -> tuple[str, str]:
    system = SYSTEM_BASE + (
        " You are the SOLVER of a ReWOO audit: the plan was executed for you; synthesize "
        "the observations into the final memo. Never request more tools."
    )
    user = (
        "Write the audit memo from these executed observations.\n"
        f"PLAN: {', '.join(plan)}\n\n"
        "OBSERVATIONS:\n" + "\n".join(observations) + "\n\n"
        f"FILING CONTEXT:\n{context}\n\n"
        "Memo format: 'Gate status' (can it be submitted/accepted, which rules block), "
        "'Anomalies' (count + largest movement), 'Checklist' (open items), "
        "'Recommendation' (one sentence). Use only figures from the observations."
    )
    return system, user
