import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { api, download, getToken, setToken } from '../client'

interface MockResponse { ok: boolean; status: number; json?: unknown; blob?: Blob; statusText?: string }

function mockFetch(response: MockResponse) {
  const fn = vi.fn(async (_url: string, _init?: RequestInit) => ({
    ok: response.ok,
    status: response.status,
    statusText: response.statusText ?? '',
    json: async () => response.json,
    blob: async () => response.blob ?? new Blob(['x']),
  }))
  vi.stubGlobal('fetch', fn)
  return fn
}

beforeEach(() => setToken(null))
afterEach(() => vi.unstubAllGlobals())

describe('centralized api client', () => {
  it('calls same-origin relative paths (proxy-friendly)', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: { status: 'ok' } })
    await api.ops.healthz()
    const [url] = fn.mock.calls[0]
    expect(url).toBe('/healthz')
  })

  it('attaches no Authorization header when logged out', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: [] })
    await api.companies.list()
    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect((init.headers as Record<string, string>)['Authorization']).toBeUndefined()
  })

  it('attaches Bearer token after setToken and clears on logout', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: [] })
    setToken('tok-123')
    expect(getToken()).toBe('tok-123')
    await api.companies.list()
    const [, init] = fn.mock.calls[0] as [string, RequestInit]
    expect((init.headers as Record<string, string>)['Authorization']).toBe('Bearer tok-123')
    setToken(null)
    expect(getToken()).toBeNull()
  })

  it('serializes JSON bodies with Content-Type', async () => {
    const fn = mockFetch({ ok: true, status: 201, json: {} })
    await api.filings.create({ company_id: 1, fiscal_year: 2026 })
    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/filings')
    expect(init.method).toBe('POST')
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json')
    expect(JSON.parse(init.body as string)).toEqual({ company_id: 1, fiscal_year: 2026 })
  })

  it('passes FormData untouched (browser sets multipart boundary)', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: {} })
    const fd = new FormData()
    fd.append('file', 'x')
    await api.trialBalance.upload(7, new File(['code,name,debit,credit'], 'tb.csv'))
    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/filings/7/trial-balance')
    expect(init.body).toBeInstanceOf(FormData)
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined()
    void fd
  })

  it('maps API errors to {status, detail}', async () => {
    mockFetch({ ok: false, status: 422, json: { detail: 'Resolve failing error-rules first: R001' } })
    await expect(api.workflow.submit(3)).rejects.toEqual({
      status: 422, detail: 'Resolve failing error-rules first: R001',
    })
  })

  it('falls back to statusText when error body is not JSON', async () => {
    const fn = vi.fn(async (_url: string, _init?: RequestInit) => ({
      ok: false, status: 500, statusText: 'Internal Server Error',
      json: async () => { throw new Error('not json') },
    }))
    vi.stubGlobal('fetch', fn)
    await expect(api.ops.healthz()).rejects.toMatchObject({ status: 500, detail: 'Internal Server Error' })
  })

  it('builds query strings for filing filters', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: [] })
    await api.filings.list({ company_id: 2, status: 'draft' })
    expect(fn.mock.calls[0][0]).toBe('/api/filings?company_id=2&status=draft')
  })

  it('fetches the cash-flow statement and ratios via the statements namespace', async () => {
    const fn = mockFetch({ ok: true, status: 200, json: [] })
    await api.statements.get(9, 'cf')
    expect(fn.mock.calls[0][0]).toBe('/api/filings/9/statements/cf')
    await api.statements.ratios(9)
    expect(fn.mock.calls[1][0]).toBe('/api/filings/9/ratios')
  })

  it('posts the ReWOO audit-memo request', async () => {
    const fn = mockFetch({
      ok: true, status: 200,
      json: { memo: '[MOCK AUDIT MEMO] …', plan: ['get_validation_report'], observations_count: 4, provider: 'mock' },
    })
    const memo = await api.ai.auditMemo(4)
    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/filings/4/audit-memo')
    expect(init.method).toBe('POST')
    expect(memo.observations_count).toBe(4)
  })

  it('download() carries the auth header and returns a Blob', async () => {
    const fn = mockFetch({ ok: true, status: 200, blob: new Blob(['pdf']) })
    setToken('dl-token')
    const blob = await download(api.exports.statementPath(5, 'pl.pdf'))
    const [url, init] = fn.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/filings/5/exports/pl.pdf')
    expect((init.headers as Record<string, string>)['Authorization']).toBe('Bearer dl-token')
    expect(blob).toBeInstanceOf(Blob)
  })
})
