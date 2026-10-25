import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth()
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 font-bold text-white">S</span>
            <span className="text-lg font-semibold text-slate-800">Financial Statement</span>
            <span className="hidden text-xs text-slate-400 sm:inline">financial statements & tax filing</span>
          </Link>
          {user && (
            <div className="flex items-center gap-3 text-sm">
              <span className="text-slate-600">{user.email}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                user.role === 'reviewer' ? 'bg-purple-100 text-purple-800' : 'bg-brand-100 text-brand-700'}`}>
                {user.role}
              </span>
              <button className="btn-ghost !px-2.5 !py-1" onClick={logout}>Log out</button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-6">{children}</main>
    </div>
  )
}
