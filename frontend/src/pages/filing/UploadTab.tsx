import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import { fmtAmount } from '../../lib/format'
import { ALL_CATEGORIES, categoryLabel } from '../../lib/categories'
import type { FilingStatus } from '../../api/types'

export default function UploadTab({ filingId, status }: { filingId: number; status: FilingStatus }) {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<unknown>(null)
  const editable = status === 'draft' || status === 'changes_requested'

  const tb = useQuery({
    queryKey: ['tb', filingId],
    queryFn: () => api.trialBalance.get(filingId),
    retry: (_count, err) => (err as { status?: number })?.status !== 404,
  })
  const invalidate = () => qc.invalidateQueries({ queryKey: ['tb', filingId] })

  const upload = useMutation({
    mutationFn: (file: File) => api.trialBalance.upload(filingId, file),
    onSuccess: invalidate, onError: setError,
  })
  const remap = useMutation({
    mutationFn: (v: { accountId: number; category: string }) => api.trialBalance.updateMapping(filingId, v.accountId, v.category),
    onSuccess: invalidate, onError: setError,
  })
  const suggest = useMutation({
    mutationFn: () => api.trialBalance.suggestMappings(filingId),
    onError: setError,
  })

  const data = tb.data
  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card flex flex-wrap items-center gap-4">
        <div>
          <h2 className="font-semibold text-slate-700">Trial balance</h2>
          <p className="text-sm text-slate-500">CSV or XLSX with columns: code, name, debit, credit. Auto-mapping applies the statutory chart of accounts.</p>
        </div>
        <input ref={fileRef} type="file" accept=".csv,.xlsx,.txt" className="text-sm" disabled={!editable}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) { setError(null); upload.mutate(f) } }} />
        {upload.isPending && <span className="text-sm text-slate-500">uploading…</span>}
        {!editable && <span className="text-xs text-amber-600">Locked while status is “{status}”.</span>}
      </div>

      {suggest.data && suggest.data.length > 0 && (
        <div className="card border-purple-200 bg-purple-50/50">
          <h3 className="mb-2 font-semibold text-purple-800">AI mapping suggestions <span className="text-xs font-normal">(review before applying — a human decides)</span></h3>
          <ul className="space-y-1.5 text-sm">
            {suggest.data.map((s) => (
              <li key={s.account_id} className="flex items-center justify-between gap-3">
                <span><b>{s.code}</b> {s.name} → <span className="font-medium text-purple-700">{categoryLabel(s.suggested_category)}</span>
                  <span className="ml-2 text-xs text-slate-500">{s.reason}</span></span>
                <button className="btn-ghost !px-2 !py-0.5 text-xs" disabled={!editable}
                  onClick={() => { setError(null); remap.mutate({ accountId: s.account_id, category: s.suggested_category }) }}>
                  Apply</button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data && (
        <div className="card">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold text-slate-700">{data.source_filename} · {data.accounts.length} accounts</h3>
            <div className="flex items-center gap-4 text-sm">
              <span>Debits <b className={data.total_debit === data.total_credit ? 'text-emerald-700' : 'text-red-600'}>{fmtAmount(data.total_debit)}</b></span>
              <span>Credits <b className={data.total_debit === data.total_credit ? 'text-emerald-700' : 'text-red-600'}>{fmtAmount(data.total_credit)}</b></span>
              {data.total_debit !== data.total_credit && <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">UNBALANCED</span>}
              {editable && data.accounts.some((a) => a.mapping_status === 'unmapped') && (
                <button className="btn-ghost" disabled={suggest.isPending}
                  onClick={() => { setError(null); suggest.mutate() }}>
                  {suggest.isPending ? 'Asking AI…' : 'Suggest mappings (AI)'}
                </button>
              )}
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr><th className="th">Code</th><th className="th">Name</th><th className="th text-right">Debit</th>
                <th className="th text-right">Credit</th><th className="th">Category</th></tr></thead>
              <tbody>
                {data.accounts.map((a) => (
                  <tr key={a.id}>
                    <td className="td font-mono">{a.code}</td>
                    <td className="td">{a.name}</td>
                    <td className="td text-right">{a.debit ? fmtAmount(a.debit) : ''}</td>
                    <td className="td text-right">{a.credit ? fmtAmount(a.credit) : ''}</td>
                    <td className="td">
                      <select className="input !w-52 !py-1" value={a.category} disabled={!editable}
                        onChange={(e) => { setError(null); remap.mutate({ accountId: a.id, category: e.target.value }) }}>
                        <option value="" disabled>— unmapped —</option>
                        {ALL_CATEGORIES.map((c) => <option key={c} value={c}>{categoryLabel(c)}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {tb.isError && (tb.error as { status?: number })?.status === 404 && (
        <div className="card text-sm text-slate-500">No trial balance uploaded yet.</div>
      )}
    </div>
  )
}
