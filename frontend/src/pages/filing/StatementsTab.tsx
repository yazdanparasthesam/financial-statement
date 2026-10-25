import { useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'
import { fmtAmount } from '../../lib/format'
import { categoryLabel } from '../../lib/categories'
import type { CashFlowData, FilingStatus, Ratio, Statement } from '../../api/types'

const PL_ORDER: { key: string; subtotal?: string }[] = [
  { key: 'revenue' }, { key: 'cogs' }, { key: 'gross_profit', subtotal: 'Gross profit' },
  { key: 'operating_expenses' }, { key: 'operating_profit', subtotal: 'Operating profit' },
  { key: 'other_income' }, { key: 'other_expenses' },
  { key: 'profit_before_tax', subtotal: 'Profit before tax' },
  { key: 'tax_expense' }, { key: 'net_profit', subtotal: 'NET PROFIT' },
]
const BS_ORDER: { key: string; subtotal?: string }[] = [
  { key: 'current_assets' }, { key: 'non_current_assets' }, { key: 'total_assets', subtotal: 'TOTAL ASSETS' },
  { key: 'current_liabilities' }, { key: 'non_current_liabilities' }, { key: 'total_liabilities', subtotal: 'Total liabilities' },
  { key: 'equity' }, { key: 'current_year_profit', subtotal: 'Current-year profit (from P&L)' },
  { key: 'total_equity', subtotal: 'Total equity' },
  { key: 'total_liabilities_and_equity', subtotal: 'TOTAL LIABILITIES & EQUITY' },
]

function StatementView({ stmt, order }: { stmt: Statement; order: typeof PL_ORDER }) {
  return (
    <table className="w-full">
      <tbody>
        {order.map(({ key, subtotal }) => {
          const node = stmt.data[key]
          if (node && typeof node === 'object' && 'items' in node) {
            const section = node as { items: { code: string; name: string; amount: number }[]; total: number }
            return (
              <FragmentRow key={key} label={categoryLabel(key)}>
                {section.items.map((it) => (
                  <tr key={it.code}><td className="td pl-8 text-slate-500">{it.code} · {it.name}</td>
                    <td className="td text-right text-slate-500">{fmtAmount(it.amount)}</td></tr>
                ))}
                <tr><td className="td font-semibold">Total {categoryLabel(key)}</td>
                  <td className="td text-right font-semibold">{fmtAmount(section.total)}</td></tr>
              </FragmentRow>
            )
          }
          if (typeof node === 'number') {
            return (
              <tr key={key} className={subtotal?.startsWith('TOTAL') || subtotal === 'NET PROFIT' ? 'bg-brand-50' : ''}>
                <td className={`td ${subtotal ? 'font-semibold' : ''}`}>{subtotal ?? categoryLabel(key)}</td>
                <td className={`td text-right ${subtotal ? 'font-semibold' : ''}`}>{fmtAmount(node)}</td>
              </tr>
            )
          }
          return null
        })}
      </tbody>
    </table>
  )
}

function FragmentRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <>
      <tr className="bg-slate-50"><td className="td font-semibold uppercase text-xs tracking-wide text-slate-600" colSpan={2}>{label}</td></tr>
      {children}
    </>
  )
}

const CF_LABELS: Record<string, string> = {
  net_profit: 'Net profit (from P&L)',
  depreciation_addback: 'Depreciation add-back',
  delta_receivables: 'Δ Receivables (rise uses cash)',
  delta_inventory: 'Δ Inventory (rise uses cash)',
  delta_payables: 'Δ Payables (rise frees cash)',
  equipment_purchases: 'Equipment purchases',
  delta_loans: 'Δ Non-current loans',
  delta_capital: 'Δ Share capital',
}

/** Cash-flow statement (indirect method) — pure arithmetic, generated server-side. */
function CashFlowView({ cf }: { cf: CashFlowData }) {
  const line = (label: string, value: number, strong = false) => (
    <tr key={label}>
      <td className={`td ${strong ? 'font-semibold' : ''}`}>{label}</td>
      <td className={`td text-right ${strong ? 'font-semibold' : ''}`}>{fmtAmount(value)}</td>
    </tr>
  )
  const reconciled = Math.abs(cf.reconciliation_gap) <= 1.0
  return (
    <table className="w-full">
      <tbody>
        <FragmentRow label="Operating activities (indirect)">
          {line(CF_LABELS.net_profit, cf.operating.net_profit)}
          {line(CF_LABELS.depreciation_addback, cf.operating.depreciation_addback)}
          {line(CF_LABELS.delta_receivables, cf.operating.delta_receivables)}
          {line(CF_LABELS.delta_inventory, cf.operating.delta_inventory)}
          {line(CF_LABELS.delta_payables, cf.operating.delta_payables)}
          {line('Net cash from operating activities', cf.operating.total, true)}
        </FragmentRow>
        <FragmentRow label="Investing activities">
          {line(CF_LABELS.equipment_purchases, cf.investing.equipment_purchases)}
          {line('Net cash from investing activities', cf.investing.total, true)}
        </FragmentRow>
        <FragmentRow label="Financing activities">
          {line(CF_LABELS.delta_loans, cf.financing.delta_loans)}
          {line(CF_LABELS.delta_capital, cf.financing.delta_capital)}
          {line('Net cash from financing activities', cf.financing.total, true)}
        </FragmentRow>
        <tr className="bg-brand-50">
          <td className="td font-semibold">NET CHANGE IN CASH</td>
          <td className="td text-right font-semibold">{fmtAmount(cf.net_change_in_cash)}</td>
        </tr>
        {line(`Cash at beginning of year`, cf.cash_begin)}
        {line(`Cash at end of year`, cf.cash_end)}
        <tr>
          <td className="td">Reconciliation gap (rule R007)</td>
          <td className="td text-right">
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${reconciled ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
              {fmtAmount(cf.reconciliation_gap)} {reconciled ? '· reconciled ✓' : '· check R007'}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  )
}

function fmtRatio(r: Ratio): string {
  if (r.value === null) return '—'
  return r.unit === '%' ? `${r.value}%` : `${r.value}${r.unit === 'x' ? '×' : ''}`
}

/** Deterministic ratios — each row shows its formula so the math is auditable. */
function RatiosPanel({ ratios }: { ratios: Ratio[] }) {
  return (
    <table className="w-full">
      <thead>
        <tr className="text-left text-xs uppercase tracking-wide text-slate-400">
          <th className="td">Ratio</th><th className="td text-right">Value</th>
          <th className="td">Formula</th><th className="td">Interpretation</th>
        </tr>
      </thead>
      <tbody>
        {ratios.map((r) => (
          <tr key={r.key}>
            <td className="td font-medium text-slate-700">{r.label}</td>
            <td className="td text-right font-semibold tabular-nums">{fmtRatio(r)}</td>
            <td className="td font-mono text-xs text-slate-500">{r.formula}</td>
            <td className="td text-xs text-slate-500">{r.interpretation}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function StatementsTab({ filingId, status }: { filingId: number; status: FilingStatus }) {
  const qc = useQueryClient()
  const [error, setError] = useState<unknown>(null)
  const noRetry404 = { retry: (_c: number, e: unknown) => (e as { status?: number })?.status !== 404 }
  const pl = useQuery({ queryKey: ['stmt', filingId, 'pl'], queryFn: () => api.statements.get(filingId, 'pl'), ...noRetry404 })
  const bs = useQuery({ queryKey: ['stmt', filingId, 'bs'], queryFn: () => api.statements.get(filingId, 'bs'), ...noRetry404 })
  const cf = useQuery({ queryKey: ['stmt', filingId, 'cf'], queryFn: () => api.statements.get(filingId, 'cf'), ...noRetry404 })
  const ratios = useQuery({ queryKey: ['ratios', filingId], queryFn: () => api.statements.ratios(filingId), ...noRetry404 })
  const generate = useMutation({
    mutationFn: () => api.statements.generate(filingId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['stmt', filingId] })
      qc.invalidateQueries({ queryKey: ['ratios', filingId] })
    },
    onError: setError,
  })
  const editable = status === 'draft' || status === 'changes_requested'

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card flex items-center justify-between">
        <p className="text-sm text-slate-500">Deterministic generation from the mapped trial balance — the AI never computes these figures.</p>
        <button className="btn-primary" disabled={generate.isPending || !editable} onClick={() => { setError(null); generate.mutate() }}>
          {generate.isPending ? 'Generating…' : 'Generate statements'}
        </button>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-2 font-semibold text-slate-700">Profit & Loss {pl.data && <span className="text-xs text-slate-400">v{pl.data.version}</span>}</h3>
          {pl.data ? <StatementView stmt={pl.data} order={PL_ORDER} /> : <p className="text-sm text-slate-400">Not generated yet.</p>}
        </div>
        <div className="card">
          <h3 className="mb-2 font-semibold text-slate-700">Balance Sheet {bs.data && <span className="text-xs text-slate-400">v{bs.data.version}</span>}</h3>
          {bs.data ? <StatementView stmt={bs.data} order={BS_ORDER} /> : <p className="text-sm text-slate-400">Not generated yet.</p>}
        </div>
        <div className="card">
          <h3 className="mb-2 font-semibold text-slate-700">
            Cash Flow (indirect) {cf.data && <span className="text-xs text-slate-400">v{cf.data.version}</span>}
          </h3>
          {cf.data
            ? <CashFlowView cf={cf.data.data as unknown as CashFlowData} />
            : <p className="text-sm text-slate-400">Needs a prior-year balance sheet — generate both years.</p>}
        </div>
        <div className="card">
          <h3 className="mb-2 font-semibold text-slate-700">Financial ratios</h3>
          {ratios.data && ratios.data.length > 0
            ? <RatiosPanel ratios={ratios.data} />
            : <p className="text-sm text-slate-400">Generated with the statements — every ratio shows its formula.</p>}
        </div>
      </div>
    </div>
  )
}
