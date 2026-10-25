import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import StatusBadge from '../../components/StatusBadge'
import { fmtDateTime } from '../../lib/format'
import { ACTION_LABELS } from '../../lib/workflow'

export default function ReviewTab({ filingId }: { filingId: number }) {
  const qc = useQueryClient()
  const [error, setError] = useState<unknown>(null)
  const [comment, setComment] = useState('')

  const filing = useQuery({ queryKey: ['filing', filingId], queryFn: () => api.filings.get(filingId) })
  const actions = useQuery({ queryKey: ['actions', filingId], queryFn: () => api.workflow.actions(filingId) })
  const events = useQuery({ queryKey: ['events', filingId], queryFn: () => api.workflow.events(filingId) })
  const comments = useQuery({ queryKey: ['comments', filingId], queryFn: () => api.workflow.comments(filingId) })

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['filing', filingId] })
    qc.invalidateQueries({ queryKey: ['actions', filingId] })
    qc.invalidateQueries({ queryKey: ['events', filingId] })
    qc.invalidateQueries({ queryKey: ['comments', filingId] })
  }
  const transition = useMutation({
    mutationFn: (v: { action: string; comment: string }) => api.workflow.transition(filingId, v.action, v.comment),
    onSuccess: refresh, onError: setError,
  })
  const addComment = useMutation({
    mutationFn: (body: string) => api.workflow.addComment(filingId, body),
    onSuccess: () => { setComment(''); qc.invalidateQueries({ queryKey: ['comments', filingId] }) },
    onError: setError,
  })
  const auditMemo = useMutation({
    mutationFn: () => api.ai.auditMemo(filingId),
    onError: setError,
  })
  const resolve = useMutation({
    mutationFn: (id: number) => api.workflow.resolveComment(filingId, id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['comments', filingId] }),
    onError: setError,
  })

  function onComment(e: FormEvent) {
    e.preventDefault()
    if (!comment.trim()) return
    setError(null)
    addComment.mutate(comment.trim())
  }

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="font-semibold text-slate-700">Workflow</h2>
          {filing.data && <StatusBadge status={filing.data.status} />}
          <div className="ml-auto flex gap-2">
            {(actions.data ?? []).map((a) => (
              <button key={a}
                className={a === 'accept' ? 'btn-primary' : a === 'reject' ? 'btn bg-red-600 text-white hover:bg-red-700' : 'btn-ghost'}
                disabled={transition.isPending}
                onClick={() => {
                  const note = window.prompt(`Optional comment for “${ACTION_LABELS[a] ?? a}”:`, '') ?? ''
                  setError(null)
                  transition.mutate({ action: a, comment: note })
                }}>
                {ACTION_LABELS[a] ?? a}
              </button>
            ))}
            {(actions.data ?? []).length === 0 && <span className="text-sm text-slate-400">No actions available for your role in this status.</span>}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-slate-700">
              AI audit memo{' '}
              <span className="text-xs font-normal text-slate-400">ReWOO agent: plan → execute read-only tools → solve</span>
            </h3>
            <p className="text-sm text-slate-500">
              Synthesizes validation, anomalies, ratios and checklist into a reviewer memo — every figure comes from
              deterministic tools, never from the model.
            </p>
          </div>
          <button className="btn-primary" disabled={auditMemo.isPending}
            onClick={() => { setError(null); auditMemo.mutate() }}>
            {auditMemo.isPending ? 'Running agent…' : 'Generate audit memo'}
          </button>
        </div>
        {auditMemo.data && (
          <div className="mt-3 space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-full bg-brand-100 px-2 py-0.5 font-semibold text-brand-700">
                provider: {auditMemo.data.provider}
              </span>
              <span className="text-slate-400">{auditMemo.data.observations_count} tool observations</span>
              {auditMemo.data.plan.map((step, i) => (
                <span key={step} className="rounded-full bg-slate-100 px-2 py-0.5 font-mono text-slate-600">
                  {i + 1}. {step}
                </span>
              ))}
            </div>
            <pre className="whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-sm text-slate-700">{auditMemo.data.memo}</pre>
          </div>
        )}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 font-semibold text-slate-700">History</h3>
          <ol className="space-y-2">
            {(events.data ?? []).map((e) => (
              <li key={e.id} className="flex items-center gap-2 text-sm">
                <span className="h-2 w-2 rounded-full bg-brand-600" />
                <span className="text-slate-400">{fmtDateTime(e.created_at)}</span>
                <span className="text-slate-600">{e.from_status} → <b>{e.to_status}</b></span>
                {e.comment && <span className="text-slate-500 italic">“{e.comment}”</span>}
              </li>
            ))}
            {(events.data ?? []).length === 0 && <li className="text-sm text-slate-400">No transitions yet.</li>}
          </ol>
        </div>
        <div className="card">
          <h3 className="mb-3 font-semibold text-slate-700">Comments</h3>
          <ul className="mb-3 space-y-2">
            {(comments.data ?? []).map((c) => (
              <li key={c.id} className={`rounded-lg border p-3 text-sm ${c.resolved ? 'border-slate-100 bg-slate-50 opacity-60' : 'border-slate-200'}`}>
                <div className="mb-1 flex items-center gap-2 text-xs text-slate-400">
                  <span>user #{c.author_id}</span><span>{fmtDateTime(c.created_at)}</span>
                  {c.anchor && <span className="font-mono">{c.anchor}</span>}
                  {c.resolved && <span className="ml-auto font-semibold text-emerald-600">resolved</span>}
                </div>
                <p className="text-slate-700">{c.body}</p>
                {!c.resolved && (
                  <button className="btn-ghost mt-2 !px-2 !py-0.5 text-xs" onClick={() => { setError(null); resolve.mutate(c.id) }}>Mark resolved</button>
                )}
              </li>
            ))}
            {(comments.data ?? []).length === 0 && <li className="text-sm text-slate-400">No comments yet.</li>}
          </ul>
          <form onSubmit={onComment} className="flex gap-2">
            <input className="input" placeholder="Add a comment…" value={comment} onChange={(e) => setComment(e.target.value)} />
            <button className="btn-ghost" disabled={addComment.isPending || !comment.trim()}>Post</button>
          </form>
        </div>
      </div>
    </div>
  )
}
