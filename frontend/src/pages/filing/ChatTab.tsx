import { useState, type FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '../../api/client'
import ErrorNote from '../../components/ErrorNote'

interface Msg { role: 'user' | 'assistant'; text: string; provider?: string }

export default function ChatTab({ filingId }: { filingId: number }) {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<unknown>(null)
  const chat = useMutation({
    mutationFn: (message: string) => api.ai.chat(filingId, message),
    onSuccess: (data) => setMessages((m) => [...m, { role: 'assistant', text: data.reply, provider: data.provider }]),
    onError: setError,
  })

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!input.trim()) return
    setMessages((m) => [...m, { role: 'user', text: input }])
    setError(null)
    chat.mutate(input.trim())
    setInput('')
  }

  return (
    <div className="space-y-4">
      <ErrorNote error={error} />
      <div className="card">
        <h2 className="font-semibold text-slate-700">Filing assistant</h2>
        <p className="text-sm text-slate-500">Grounded on this filing's statements and validation results. Identifiers (national ID, economic code) are redacted before leaving the server.</p>
      </div>
      <div className="card space-y-3">
        {messages.length === 0 && <p className="text-sm text-slate-400">Ask something like “Why did revenue jump?” or “What blocks submission?”</p>}
        {messages.map((m, i) => (
          <div key={i} className={`max-w-[85%] rounded-xl px-4 py-2.5 text-sm ${
            m.role === 'user' ? 'ml-auto bg-brand-600 text-white' : 'bg-slate-100 text-slate-700'}`}>
            {m.text}
            {m.provider && <div className="mt-1 text-[10px] uppercase tracking-wide opacity-60">via {m.provider}</div>}
          </div>
        ))}
        {chat.isPending && <div className="text-sm text-slate-400">assistant is typing…</div>}
        <form onSubmit={onSubmit} className="flex gap-2 pt-2">
          <input className="input" placeholder="Your question…" value={input} onChange={(e) => setInput(e.target.value)} />
          <button className="btn-primary" disabled={chat.isPending || !input.trim()}>Send</button>
        </form>
      </div>
    </div>
  )
}
