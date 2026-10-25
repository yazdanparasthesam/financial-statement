/**
 * CENTRALIZED backend client — every HTTP call in the app goes through this module
 * (criterion 4: "centralized backend communication"). Pages/components never call
 * fetch() directly.
 *
 * Base URL: VITE_API_URL if set (prod static hosting), otherwise same-origin ''
 * (vite dev proxy / nginx in docker compose forward /api to the backend).
 */
import type {
  Anomaly, ApiError, AuditMemo, ChatOut, ChecklistItem, Company, Deadline, ExplainOut, Filing,
  MappingSuggestion, Note, Ratio, ReviewComment, ReviewEvent, Role, Statement, TokenOut,
  TrialBalance, User, ValidationRun,
} from './types'

const TOKEN_KEY = 'fs_token'
const BASE = ((import.meta.env?.VITE_API_URL as string | undefined) ?? '').replace(/\/$/, '')

const storage: Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> | null =
  typeof localStorage !== 'undefined' ? localStorage : null

let token: string | null = storage?.getItem(TOKEN_KEY) ?? null

export function setToken(t: string | null): void {
  token = t
  if (t) storage?.setItem(TOKEN_KEY, t)
  else storage?.removeItem(TOKEN_KEY)
}
export function getToken(): string | null { return token }

async function request<T>(method: string, path: string, body?: unknown, isForm = false): Promise<T> {
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isForm ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      if (typeof data?.detail === 'string') detail = data.detail
      else if (data?.detail) detail = JSON.stringify(data.detail)
    } catch { /* keep statusText */ }
    throw { status: res.status, detail } as ApiError
  }
  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

/** Authenticated blob download (exports) — window.open can't carry the Bearer header. */
export async function download(path: string): Promise<Blob> {
  const headers: Record<string, string> = {}
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { headers })
  if (!res.ok) throw { status: res.status, detail: `Download failed: ${res.statusText}` } as ApiError
  return res.blob()
}

export const api = {
  request,
  download,
  auth: {
    register: (d: { email: string; password: string; full_name?: string; role?: Role }) =>
      request<User>('POST', '/api/auth/register', d),
    login: (d: { email: string; password: string }) => request<TokenOut>('POST', '/api/auth/login', d),
    me: () => request<User>('GET', '/api/auth/me'),
  },
  companies: {
    list: () => request<Company[]>('GET', '/api/companies'),
    create: (d: { name: string; national_id?: string; economic_code?: string; fiscal_year_end_month?: number }) =>
      request<Company>('POST', '/api/companies', d),
  },
  filings: {
    list: (params?: { company_id?: number; status?: string }) => {
      const q = new URLSearchParams()
      if (params?.company_id) q.set('company_id', String(params.company_id))
      if (params?.status) q.set('status', params.status)
      const s = q.toString()
      return request<Filing[]>('GET', `/api/filings${s ? `?${s}` : ''}`)
    },
    create: (d: { company_id: number; fiscal_year: number }) => request<Filing>('POST', '/api/filings', d),
    get: (id: number) => request<Filing>('GET', `/api/filings/${id}`),
    deadline: (id: number) => request<Deadline>('GET', `/api/filings/${id}/deadline`),
  },
  trialBalance: {
    get: (filingId: number) => request<TrialBalance>('GET', `/api/filings/${filingId}/trial-balance`),
    upload: (filingId: number, file: File) => {
      const fd = new FormData()
      fd.append('file', file)
      return request<TrialBalance>('POST', `/api/filings/${filingId}/trial-balance`, fd, true)
    },
    updateMapping: (filingId: number, accountId: number, category: string) =>
      request<import('./types').TBAccount>(
        'PATCH', `/api/filings/${filingId}/trial-balance/accounts/${accountId}`, { category }),
    suggestMappings: (filingId: number) =>
      request<MappingSuggestion[]>('POST', `/api/filings/${filingId}/trial-balance/suggest-mappings`),
  },
  statements: {
    generate: (filingId: number) => request<Statement[]>('POST', `/api/filings/${filingId}/statements/generate`),
    get: (filingId: number, kind: 'pl' | 'bs' | 'cf') =>
      request<Statement>('GET', `/api/filings/${filingId}/statements/${kind}`),
    ratios: (filingId: number) => request<Ratio[]>('GET', `/api/filings/${filingId}/ratios`),
  },
  validation: {
    run: (filingId: number) => request<ValidationRun>('POST', `/api/filings/${filingId}/validate`),
    latest: (filingId: number) => request<ValidationRun>('GET', `/api/filings/${filingId}/validations/latest`),
    anomalies: (filingId: number) => request<Anomaly[]>('GET', `/api/filings/${filingId}/anomalies`),
  },
  ai: {
    explainAnomaly: (anomalyId: number) => request<ExplainOut>('POST', `/api/anomalies/${anomalyId}/explain`),
    listNotes: (filingId: number) => request<Note[]>('GET', `/api/filings/${filingId}/notes`),
    draftNote: (filingId: number, section: string) =>
      request<Note>('POST', `/api/filings/${filingId}/notes/draft`, { section }),
    finalizeNote: (noteId: number, final_text: string) =>
      request<Note>('PATCH', `/api/notes/${noteId}`, { final_text }),
    chat: (filingId: number, message: string) =>
      request<ChatOut>('POST', `/api/filings/${filingId}/assistant/chat`, { message }),
    auditMemo: (filingId: number) => request<AuditMemo>('POST', `/api/filings/${filingId}/audit-memo`),
  },
  workflow: {
    submit: (filingId: number) => request<Filing>('POST', `/api/filings/${filingId}/submit`),
    transition: (filingId: number, action: string, comment = '') =>
      request<Filing>('POST', `/api/filings/${filingId}/review/transition`, { action, comment }),
    actions: (filingId: number) => request<string[]>('GET', `/api/filings/${filingId}/review/actions`),
    events: (filingId: number) => request<ReviewEvent[]>('GET', `/api/filings/${filingId}/review/events`),
    comments: (filingId: number) => request<ReviewComment[]>('GET', `/api/filings/${filingId}/comments`),
    addComment: (filingId: number, body: string, anchor = '') =>
      request<ReviewComment>('POST', `/api/filings/${filingId}/comments`, { body, anchor }),
    resolveComment: (filingId: number, commentId: number) =>
      request<ReviewComment>('PATCH', `/api/filings/${filingId}/comments/${commentId}/resolve`),
  },
  exports: {
    checklist: (filingId: number) => request<ChecklistItem[]>('GET', `/api/filings/${filingId}/checklist`),
    statementPath: (filingId: number, filename: string) => `/api/filings/${filingId}/exports/${filename}`,
    checklistPdfPath: (filingId: number) => `/api/filings/${filingId}/exports/checklist.pdf`,
  },
  ops: {
    healthz: () => request<{ status: string }>('GET', '/healthz'),
    version: () => request<{ app: string; version: string; ai_provider: string }>('GET', '/version'),
  },
}
