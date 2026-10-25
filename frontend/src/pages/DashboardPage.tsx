import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import Layout from '../components/Layout'
import StatusBadge from '../components/StatusBadge'
import ErrorNote from '../components/ErrorNote'
import { daysLabel } from '../lib/format'

export default function DashboardPage() {
  const qc = useQueryClient()
  const companies = useQuery({ queryKey: ['companies'], queryFn: api.companies.list })
  const filings = useQuery({ queryKey: ['filings'], queryFn: () => api.filings.list() })
  const [error, setError] = useState<unknown>(null)

  const [companyForm, setCompanyForm] = useState({ name: '', national_id: '', fiscal_year_end_month: 3 })
  const createCompany = useMutation({
    mutationFn: api.companies.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['companies'] }); setCompanyForm({ name: '', national_id: '', fiscal_year_end_month: 3 }) },
    onError: setError,
  })

  const [filingForm, setFilingForm] = useState({ company_id: 0, fiscal_year: new Date().getFullYear() })
  const createFiling = useMutation({
    mutationFn: api.filings.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['filings'] }) },
    onError: setError,
  })

  function onCompany(e: FormEvent) { e.preventDefault(); setError(null); createCompany.mutate(companyForm) }
  function onFiling(e: FormEvent) { e.preventDefault(); setError(null); createFiling.mutate(filingForm) }

  return (
    <Layout>
      <h1 className="mb-4 text-2xl font-semibold text-slate-800">Dashboard</h1>
      <ErrorNote error={error} />
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <form onSubmit={onCompany} className="card space-y-3">
          <h2 className="font-semibold text-slate-700">New company</h2>
          <div><label className="label">Name</label>
            <input className="input" value={companyForm.name} required
              onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })} /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">National ID</label>
              <input className="input" value={companyForm.national_id}
                onChange={(e) => setCompanyForm({ ...companyForm, national_id: e.target.value })} /></div>
            <div><label className="label">FY end month</label>
              <input className="input" type="number" min={1} max={12} value={companyForm.fiscal_year_end_month}
                onChange={(e) => setCompanyForm({ ...companyForm, fiscal_year_end_month: Number(e.target.value) })} /></div>
          </div>
          <button className="btn-primary" disabled={createCompany.isPending}>Add company</button>
        </form>

        <form onSubmit={onFiling} className="card space-y-3">
          <h2 className="font-semibold text-slate-700">New filing</h2>
          <div><label className="label">Company</label>
            <select className="input" value={filingForm.company_id} required
              onChange={(e) => setFilingForm({ ...filingForm, company_id: Number(e.target.value) })}>
              <option value={0} disabled>Select company…</option>
              {(companies.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select></div>
          <div><label className="label">Fiscal year (start year)</label>
            <input className="input" type="number" min={2000} max={2100} value={filingForm.fiscal_year}
              onChange={(e) => setFilingForm({ ...filingForm, fiscal_year: Number(e.target.value) })} /></div>
          <button className="btn-primary" disabled={createFiling.isPending || !filingForm.company_id}>Create filing</button>
        </form>
      </div>

      <div className="card">
        <h2 className="mb-3 font-semibold text-slate-700">Filings</h2>
        <table className="w-full">
          <thead><tr><th className="th">ID</th><th className="th">Company</th><th className="th">Fiscal year</th>
            <th className="th">Deadline</th><th className="th">Status</th><th className="th" /></tr></thead>
          <tbody>
            {(filings.data ?? []).map((f) => {
              const company = (companies.data ?? []).find((c) => c.id === f.company_id)
              const days = f.deadline ? Math.round((new Date(f.deadline).getTime() - Date.now()) / 86400000) : null
              return (
                <tr key={f.id} className="hover:bg-slate-50">
                  <td className="td">#{f.id}</td>
                  <td className="td">{company?.name ?? `company ${f.company_id}`}</td>
                  <td className="td">{f.fiscal_year}</td>
                  <td className="td">{f.deadline}{days !== null && <span className={`ml-2 text-xs ${days < 0 ? 'text-red-600' : 'text-slate-500'}`}>{daysLabel(days)}</span>}</td>
                  <td className="td"><StatusBadge status={f.status} /></td>
                  <td className="td text-right">
                    <Link className="btn-ghost !px-2.5 !py-1" to={`/filings/${f.id}`}>Open</Link></td>
                </tr>
              )
            })}
            {(filings.data ?? []).length === 0 && (
              <tr><td className="td text-slate-400" colSpan={6}>No filings yet — create a company and a filing above.</td></tr>)}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
