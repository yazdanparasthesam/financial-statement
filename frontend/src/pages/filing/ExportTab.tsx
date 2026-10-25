import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, download } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'

async function saveBlob(path: string, filename: string) {
  const blob = await download(path)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function ExportTab({ filingId }: { filingId: number }) {
  const [error, setError] = useState<unknown>(null)
  const [busy, setBusy] = useState('')
  const checklist = useQuery({ queryKey: ['checklist', filingId], queryFn: () => api.exports.checklist(filingId) })

  async function doDownload(path: string, filename: string) {
    setBusy(filename); setError(null)
    try { await saveBlob(path, filename) } catch (e) { setError(e) } finally { setBusy('') }
  }

  const files = [
    { filename: 'pl.pdf', label: 'Profit & Loss — PDF' },
    { filename: 'pl.xlsx', label: 'Profit & Loss — Excel' },
    { filename: 'bs.pdf', label: 'Balance Sheet — PDF' },
    { filename: 'bs.xlsx', label: 'Balance Sheet — Excel' },
  ]

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-700">Filing checklist</h2>
        <ul className="space-y-1.5">
          {(checklist.data ?? []).map((c) => (
            <li key={c.item} className="flex items-center gap-2 text-sm">
              <span className={`grid h-5 w-5 place-items-center rounded border text-xs font-bold ${
                c.done ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-slate-300 text-transparent'}`}>✓</span>
              <span className={c.done ? 'text-slate-700' : 'text-slate-400'}>{c.item}</span>
            </li>
          ))}
        </ul>
        <button className="btn-ghost mt-4" disabled={busy === 'checklist.pdf'}
          onClick={() => doDownload(api.exports.checklistPdfPath(filingId), 'checklist.pdf')}>
          Download checklist (PDF)
        </button>
      </div>
      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-700">Statement exports</h2>
        <div className="flex flex-wrap gap-2">
          {files.map((f) => (
            <button key={f.filename} className="btn-ghost" disabled={busy === f.filename}
              onClick={() => doDownload(api.exports.statementPath(filingId, f.filename), f.filename)}>
              {busy === f.filename ? 'Preparing…' : f.label}
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-400">Downloads carry the Bearer token via fetch — no unauthenticated file access.</p>
      </div>
    </div>
  )
}
