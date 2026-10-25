import type { FilingStatus } from '../api/types'
import { STATUS_META } from '../lib/workflow'

export default function StatusBadge({ status }: { status: FilingStatus }) {
  const meta = STATUS_META[status] ?? { label: status, badge: 'bg-slate-200 text-slate-700' }
  return <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${meta.badge}`}>{meta.label}</span>
}
