/** Number/date formatting helpers (pure — covered by vitest). */
export function fmtAmount(n: number): string {
  return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
export function fmtPct(pct: number): string {
  return `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`
}
export function daysLabel(days: number): string {
  if (days < 0) return `${-days}d overdue`
  if (days === 0) return 'due today'
  return `${days}d left`
}
export function fmtDateTime(iso: string): string {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
}
