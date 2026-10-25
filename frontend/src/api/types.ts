// Types mirror openapi.yaml (the contract). If the contract changes, change these.
export type Role = 'preparer' | 'reviewer'
export type FilingStatus = 'draft' | 'submitted' | 'in_review' | 'changes_requested' | 'accepted' | 'rejected'
export type Severity = 'error' | 'warning' | 'info'

export interface User { id: number; email: string; full_name: string; role: Role }
export interface TokenOut { access_token: string; token_type: string; user: User }
export interface Company {
  id: number; name: string; national_id: string; economic_code: string
  fiscal_year_end_month: number; owner_id: number
}
export interface Filing {
  id: number; company_id: number; fiscal_year: number; status: FilingStatus
  deadline: string; created_at: string; updated_at: string
}
export interface Deadline { fiscal_year: number; deadline: string; days_remaining: number }
export interface TBAccount {
  id: number; code: string; name: string; debit: number; credit: number
  category: string; mapping_status: 'mapped' | 'unmapped'
}
export interface TrialBalance {
  id: number; source_filename: string; total_debit: number; total_credit: number
  imported_at: string; accounts: TBAccount[]
}
export interface MappingSuggestion {
  account_id: number; code: string; name: string; suggested_category: string; reason: string
}
export interface StatementSection { items: { code: string; name: string; amount: number }[]; total: number }
export interface Statement {
  id: number; kind: 'pl' | 'bs' | 'cf'; version: number; generated_at: string
  data: Record<string, StatementSection | number>
}
/** Shape of a cash-flow statement's `data` (indirect method, domain/cashflow.py). */
export interface CashFlowData {
  operating: {
    net_profit: number; depreciation_addback: number; delta_receivables: number
    delta_inventory: number; delta_payables: number; total: number
  }
  investing: { equipment_purchases: number; total: number }
  financing: { delta_loans: number; delta_capital: number; total: number }
  net_change_in_cash: number; cash_begin: number; cash_end: number; reconciliation_gap: number
}
export interface Ratio {
  key: string; label: string; value: number | null; unit: string
  formula: string; interpretation: string
}
export interface AuditMemo { memo: string; plan: string[]; observations_count: number; provider: string }
export interface ValidationResult {
  rule_id: string; severity: Severity; passed: boolean; message: string
  context?: Record<string, unknown> | null
}
export interface ValidationRun {
  id: number; run_at: string; passed: number; failed: number; results: ValidationResult[]
}
export interface Anomaly {
  id: number; account_code: string; account_name: string; metric: string
  prior_value: number; current_value: number; pct_change: number
  ai_explanation: string; dismissed: boolean
}
export interface ExplainOut { anomaly_id: number; explanation: string; provider: string }
export interface Note { id: number; section: string; draft_text: string; final_text: string; ai_generated: boolean }
export interface ChatOut { reply: string; provider: string }
export interface ReviewEvent {
  id: number; actor_id: number; from_status: FilingStatus; to_status: FilingStatus
  comment: string; created_at: string
}
export interface ReviewComment {
  id: number; author_id: number; anchor: string; body: string; resolved: boolean; created_at: string
}
export interface ChecklistItem { item: string; done: boolean }
export interface ApiError { status: number; detail: string }
