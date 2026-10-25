import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import ErrorNote from '../components/ErrorNote'

export default function RegisterPage() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [form, setForm] = useState({ email: '', password: '', full_name: '', role: 'preparer' as 'preparer' | 'reviewer' })
  const [error, setError] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await register(form); nav('/login') }
    catch (err) { setError(err) }
    finally { setBusy(false) }
  }

  return (
    <div className="grid min-h-screen place-items-center p-6">
      <form onSubmit={onSubmit} className="card w-full max-w-sm space-y-4">
        <h1 className="text-xl font-semibold text-slate-800">Create account</h1>
        <ErrorNote error={error} />
        <div><label className="label">Full name</label>
          <input className="input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} /></div>
        <div><label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
        <div><label className="label">Password (min 8 chars)</label>
          <input className="input" type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></div>
        <div><label className="label">Role</label>
          <select className="input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as 'preparer' | 'reviewer' })}>
            <option value="preparer">Preparer (accountant / company)</option>
            <option value="reviewer">Reviewer (senior accountant)</option>
          </select></div>
        <button className="btn-primary w-full justify-center" disabled={busy}>{busy ? 'Creating…' : 'Register'}</button>
        <p className="text-center text-sm text-slate-500">Have an account? <Link className="text-brand-600 underline" to="/login">Sign in</Link></p>
      </form>
    </div>
  )
}
