import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import { categoryLabel } from '../../lib/categories'
import { ALL_CATEGORIES } from '../../lib/categories'

export default function NotesTab({ filingId }: { filingId: number }) {
  const qc = useQueryClient()
  const [section, setSection] = useState('revenue')
  const [error, setError] = useState<unknown>(null)
  const notes = useQuery({ queryKey: ['notes', filingId], queryFn: () => api.ai.listNotes(filingId) })
  const invalidate = () => qc.invalidateQueries({ queryKey: ['notes', filingId] })

  const draft = useMutation({ mutationFn: () => api.ai.draftNote(filingId, section), onSuccess: invalidate, onError: setError })
  const [savingId, setSavingId] = useState<number | null>(null)
  const save = useMutation({
    mutationFn: (v: { id: number; text: string }) => api.ai.finalizeNote(v.id, v.text),
    onSuccess: invalidate, onError: setError,
  })

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card flex flex-wrap items-end gap-3">
        <div>
          <h2 className="font-semibold text-slate-700">Notes to the accounts</h2>
          <p className="text-sm text-slate-500">AI drafts from the generated figures; the preparer edits and <b>finalizes</b> — drafts are marked until saved.</p>
        </div>
        <div className="ml-auto flex items-end gap-2">
          <div>
            <label className="label">Section</label>
            <select className="input !w-56" value={section} onChange={(e) => setSection(e.target.value)}>
              {[...ALL_CATEGORIES, 'general'].map((s) => <option key={s} value={s}>{categoryLabel(s)}</option>)}
            </select>
          </div>
          <button className="btn-primary" disabled={draft.isPending} onClick={() => { setError(null); draft.mutate() }}>
            {draft.isPending ? 'Drafting…' : 'Draft with AI'}
          </button>
        </div>
      </div>

      {(notes.data ?? []).length === 0 && <div className="card text-sm text-slate-500">No notes yet.</div>}
      {(notes.data ?? []).map((n) => (
        <div key={n.id} className="card space-y-2">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-700">{categoryLabel(n.section)}</h3>
            {n.ai_generated && !n.final_text && <span className="rounded bg-purple-100 px-2 py-0.5 text-xs font-semibold text-purple-700">AI draft</span>}
            {n.final_text && <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">finalized</span>}
          </div>
          {n.draft_text && <p className="rounded-lg bg-slate-50 p-3 text-sm text-slate-500">{n.draft_text}</p>}
          <textarea className="input min-h-24" defaultValue={n.final_text || n.draft_text}
            onChange={() => setSavingId(n.id)} data-note={n.id}
            onBlur={(e) => {
              const text = e.target.value
              if (text !== n.final_text) { setError(null); save.mutate({ id: n.id, text }) }
              setSavingId(null)
            }} />
          <div className="flex justify-end">
            <button className="btn-ghost" disabled={save.isPending}
              onClick={() => {
                const el = document.querySelector(`[data-note="${n.id}"]`) as HTMLTextAreaElement | null
                if (el) { setError(null); save.mutate({ id: n.id, text: el.value }) }
              }}>
              {savingId === n.id && save.isPending ? 'Saving…' : 'Save final text'}
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
