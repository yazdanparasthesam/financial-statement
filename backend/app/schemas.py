"""Pydantic request/response schemas — mirrored by openapi.yaml (contract drift = CI red)."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- auth ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = ""
    role: str = "preparer"  # preparer | reviewer


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- companies ----------
class CompanyCreate(BaseModel):
    name: str
    national_id: str = ""
    economic_code: str = ""
    fiscal_year_end_month: int = Field(default=3, ge=1, le=12)


class CompanyOut(BaseModel):
    id: int
    name: str
    national_id: str
    economic_code: str
    fiscal_year_end_month: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


# ---------- filings ----------
class FilingCreate(BaseModel):
    company_id: int
    fiscal_year: int = Field(ge=2000, le=2100)


class FilingOut(BaseModel):
    id: int
    company_id: int
    fiscal_year: int
    status: str
    deadline: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeadlineOut(BaseModel):
    fiscal_year: int
    deadline: str
    days_remaining: int


# ---------- trial balance ----------
class TBAccountOut(BaseModel):
    id: int
    code: str
    name: str
    debit: float
    credit: float
    category: str
    mapping_status: str

    model_config = ConfigDict(from_attributes=True)


class TrialBalanceOut(BaseModel):
    id: int
    source_filename: str
    total_debit: float
    total_credit: float
    imported_at: datetime
    accounts: list[TBAccountOut] = []


class MappingUpdate(BaseModel):
    category: str


class MappingSuggestion(BaseModel):
    account_id: int
    code: str
    name: str
    suggested_category: str
    reason: str


# ---------- statements / validation ----------
class StatementOut(BaseModel):
    id: int
    kind: str
    version: int
    generated_at: datetime
    data: dict[str, Any]


class ValidationResultOut(BaseModel):
    rule_id: str
    severity: str
    passed: bool
    message: str
    context: dict[str, Any] | None = None


class ValidationRunOut(BaseModel):
    id: int
    run_at: datetime
    passed: int
    failed: int
    results: list[ValidationResultOut] = []


class RatioOut(BaseModel):
    key: str
    label: str
    value: float | None
    unit: str
    formula: str
    interpretation: str


class AnomalyOut(BaseModel):
    id: int
    account_code: str
    account_name: str
    metric: str
    prior_value: float
    current_value: float
    pct_change: float
    ai_explanation: str
    dismissed: bool

    model_config = ConfigDict(from_attributes=True)


class ExplainOut(BaseModel):
    anomaly_id: int
    explanation: str
    provider: str


# ---------- notes / chat ----------
class NoteDraftIn(BaseModel):
    section: str


class NoteOut(BaseModel):
    id: int
    section: str
    draft_text: str
    final_text: str
    ai_generated: bool

    model_config = ConfigDict(from_attributes=True)


class NoteUpdate(BaseModel):
    final_text: str


class ChatIn(BaseModel):
    message: str


class ChatOut(BaseModel):
    reply: str
    provider: str


class AuditMemoOut(BaseModel):
    memo: str
    plan: list[str]
    observations_count: int
    provider: str


# ---------- workflow ----------
class TransitionIn(BaseModel):
    action: str
    comment: str = ""


class ReviewEventOut(BaseModel):
    id: int
    actor_id: int
    from_status: str
    to_status: str
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    body: str
    anchor: str = ""


class CommentOut(BaseModel):
    id: int
    author_id: int
    anchor: str
    body: str
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- exports / ops ----------
class ChecklistItem(BaseModel):
    item: str
    done: bool


class HealthOut(BaseModel):
    status: str = "ok"


class VersionOut(BaseModel):
    app: str
    version: str
    ai_provider: str
