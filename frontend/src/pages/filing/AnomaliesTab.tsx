import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import { fmtAmount, fmtPct } from '../../lib/format'

export default function AnomaliesTab({ filingId }: { filingId: number }) {
  const qc = useQueryClient()
  const [error, setError] = useState<unknown>(null)
  const anomalies = useQuery({ queryKey: ['anomalies', filingId], queryFn: () => api.validation.anomalies(filingId) })
  const explain = useMutation({
    mutationFn: (id: number) => api.ai.explainAnomaly(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['anomalies', filingId] }),
    onError: setError,
  })

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card">
        <h2 className="font-semibold text-slate-700">Year-over-year anomalies</h2>
        <p className="text-sm text-slate-500">Flagged deterministically (|Δ| &gt; 50% vs prior-year statements). The AI only <i>explains</i> — numbers come from the engine.</p>
      </div>
      {(anomalies.data ?? []).length === 0 && (
        <div className="card text-sm text-slate-500">No anomalies flagged. Run validation after uploading two consecutive years to compare.</div>
      )}
      {(anomalies.data ?? []).map((a) => (
        <div key={a.id} className="card">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono text-xs text-slate-400">{a.account_code}</span>
            <h3 className="font-semibold text-slate-700">{a.account_name}</h3>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${Math.abs(a.pct_change) > 100 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{fmtPct(a.pct_change)}</span>
            <span className="text-sm text-slate-500">{fmtAmount(a.prior_value)} → {fmtAmount(a.current_value)}</span>
            <button className="btn-ghost ml-auto" disabled={explain.isPending}
              onClick={() => { setError(null); explain.mutate(a.id) }}>
              {explain.isPending ? 'Asking AI…' : a.ai_explanation ? 'Re-explain (AI)' : 'Explain (AI)'}
            </button>
          </div>
          {a.ai_explanation && (
            <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">{a.ai_explanation}</p>
          )}
        </div>
      ))}
    </div>
  )
}
