import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import Layout from '../components/Layout'
import Spinner from '../components/Spinner'
import ErrorNote from '../components/ErrorNote'
import StatusBadge from '../components/StatusBadge'
import Tabs from '../components/Tabs'
import { daysLabel } from '../lib/format'
import { STATUS_META } from '../lib/workflow'
import UploadTab from './filing/UploadTab'
import StatementsTab from './filing/StatementsTab'
import ValidationTab from './filing/ValidationTab'
import AnomaliesTab from './filing/AnomaliesTab'
import NotesTab from './filing/NotesTab'
import ChatTab from './filing/ChatTab'
import ReviewTab from './filing/ReviewTab'
import ExportTab from './filing/ExportTab'

const TABS = [
  { id: 'upload', label: '1 · Trial balance' },
  { id: 'statements', label: '2 · Statements' },
  { id: 'validation', label: '3 · Validation' },
  { id: 'anomalies', label: '4 · Anomalies (AI)' },
  { id: 'notes', label: '5 · Notes (AI)' },
  { id: 'chat', label: '6 · Assistant (AI)' },
  { id: 'review', label: '7 · Review' },
  { id: 'export', label: '8 · Export' },
]

export default function FilingPage() {
  const { id } = useParams()
  const filingId = Number(id)
  const [tab, setTab] = useState('upload')
  const filing = useQuery({ queryKey: ['filing', filingId], queryFn: () => api.filings.get(filingId) })
  const deadline = useQuery({ queryKey: ['deadline', filingId], queryFn: () => api.filings.deadline(filingId) })

  if (filing.isLoading) return <Layout><Spinner /></Layout>
  if (filing.error) return <Layout><ErrorNote error={filing.error} /><Link className="btn-ghost mt-4" to="/">← Back</Link></Layout>
  const f = filing.data!

  return (
    <Layout>
      <div className="mb-1 flex items-center gap-3">
        <Link to="/" className="text-sm text-slate-500 hover:underline">← Dashboard</Link>
      </div>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">Filing #{f.id} · FY {f.fiscal_year}</h1>
        <StatusBadge status={f.status} />
        {deadline.data && (
          <span className="text-sm text-slate-500">
            deadline {deadline.data.deadline} ({daysLabel(deadline.data.days_remaining)})
          </span>
        )}
      </div>
      <p className="mb-5 text-sm text-slate-500">{STATUS_META[f.status]?.desc}</p>
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      {tab === 'upload' && <UploadTab filingId={filingId} status={f.status} />}
      {tab === 'statements' && <StatementsTab filingId={filingId} status={f.status} />}
      {tab === 'validation' && <ValidationTab filingId={filingId} />}
      {tab === 'anomalies' && <AnomaliesTab filingId={filingId} />}
      {tab === 'notes' && <NotesTab filingId={filingId} />}
      {tab === 'chat' && <ChatTab filingId={filingId} />}
      {tab === 'review' && <ReviewTab filingId={filingId} />}
      {tab === 'export' && <ExportTab filingId={filingId} />}
    </Layout>
  )
}
