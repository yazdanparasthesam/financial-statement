import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import { severityBadge, summarize } from '../../lib/validation'

const RULE_NAMES: Record<string, string> = {
  R001: 'Trial balance balanced', R002: 'Balance-sheet identity (A = L + E)',
  R003: 'All accounts mapped', R004: 'Revenue present',
  R005: 'Equity positive', R006: 'Year-over-year anomalies',
}

export default function ValidationTab({ filingId }: { filingId: number }) {
  const qc = useQueryClient()
  const [error, setError] = useState<unknown>(null)
  const latest = useQuery({
    queryKey: ['validation', filingId],
    queryFn: () => api.validation.latest(filingId),
    retry: (_c, e) => (e as { status?: number })?.status !== 404,
  })
  const run = useMutation({
    mutationFn: () => api.validation.run(filingId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['validation', filingId] }),
    onError: setError,
  })
  const summary = latest.data ? summarize(latest.data.results) : null

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-slate-700">Deterministic validation engine</h2>
          <p className="text-sm text-slate-500">Six statutory rules. Failing <b>error</b>-level rules block submission; warnings are surfaced to the reviewer.</p>
        </div>
        <button className="btn-primary" disabled={run.isPending} onClick={() => { setError(null); run.mutate() }}>
          {run.isPending ? 'Running…' : 'Run validation'}
        </button>
      </div>

      {summary && latest.data && (
        <>
          <div className={`card ${summary.canSubmit ? 'border-emerald-200' : 'border-red-200'}`}>
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <span className="font-semibold">{summary.passed}/{summary.total} rules passed</span>
              {summary.failedErrors.length > 0 && <span className="rounded bg-red-100 px-2 py-0.5 font-semibold text-red-700">BLOCKED: {summary.failedErrors.map((e) => e.rule_id).join(', ')}</span>}
              {summary.failedWarnings.length > 0 && <span className="rounded bg-amber-100 px-2 py-0.5 font-semibold text-amber-700">{summary.failedWarnings.length} warning(s)</span>}
              {summary.canSubmit && summary.failedWarnings.length === 0 && <span className="rounded bg-emerald-100 px-2 py-0.5 font-semibold text-emerald-700">CLEAN — ready to submit</span>}
              <span className="ml-auto text-xs text-slate-400">run at {new Date(latest.data.run_at).toLocaleString('en-GB')}</span>
            </div>
          </div>
          <div className="card">
            <table className="w-full">
              <thead><tr><th className="th">Rule</th><th className="th">Check</th><th className="th">Severity</th><th className="th">Result</th><th className="th">Message</th></tr></thead>
              <tbody>
                {latest.data.results.map((r) => (
                  <tr key={r.rule_id}>
                    <td className="td font-mono">{r.rule_id}</td>
                    <td className="td">{RULE_NAMES[r.rule_id] ?? r.rule_id}</td>
                    <td className="td"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${severityBadge(r.severity)}`}>{r.severity}</span></td>
                    <td className="td">{r.passed ? <span className="font-semibold text-emerald-600">PASS</span> : <span className="font-semibold text-red-600">FAIL</span>}</td>
                    <td className="td text-slate-600">{r.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      {latest.isError && (latest.error as { status?: number })?.status === 404 && (
        <div className="card text-sm text-slate-500">Validation has not been run yet.</div>
      )}
    </div>
  )
}
