import type { ApiError } from '../api/types'

export default function ErrorNote({ error }: { error: unknown }) {
  if (!error) return null
  const e = error as ApiError
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {e.detail ?? String(error)}
      {e.status ? <span className="ml-2 text-xs opacity-70">(HTTP {e.status})</span> : null}
    </div>
  )
}
