/**
 * Client-side mirror of the backend state machine (app/domain/workflow.py).
 * UI hint only — the server ALWAYS re-validates transitions and roles.
 */
import type { FilingStatus, Role } from '../api/types'

export const STATUS_META: Record<FilingStatus, { label: string; badge: string; desc: string }> = {
  draft: { label: 'Draft', badge: 'bg-slate-200 text-slate-700', desc: 'Being prepared; uploads and regeneration allowed.' },
  submitted: { label: 'Submitted', badge: 'bg-blue-100 text-blue-800', desc: 'Waiting for a reviewer to pick it up.' },
  in_review: { label: 'In review', badge: 'bg-amber-100 text-amber-800', desc: 'Reviewer is examining the statements.' },
  changes_requested: { label: 'Changes requested', badge: 'bg-orange-100 text-orange-800', desc: 'Preparer must fix and reopen.' },
  accepted: { label: 'Accepted', badge: 'bg-emerald-100 text-emerald-800', desc: 'Ready to file with the tax authority.' },
  rejected: { label: 'Rejected', badge: 'bg-red-100 text-red-800', desc: 'Rejected by reviewer; see comments.' },
}

type Transition = [from: FilingStatus, to: FilingStatus, role: Role]
const TRANSITIONS: Record<string, Transition> = {
  submit: ['draft', 'submitted', 'preparer'],
  reopen: ['changes_requested', 'draft', 'preparer'],
  start_review: ['submitted', 'in_review', 'reviewer'],
  request_changes: ['in_review', 'changes_requested', 'reviewer'],
  accept: ['in_review', 'accepted', 'reviewer'],
  reject: ['in_review', 'rejected', 'reviewer'],
}

export const ACTION_LABELS: Record<string, string> = {
  submit: 'Submit for review',
  reopen: 'Reopen as draft',
  start_review: 'Start review',
  request_changes: 'Request changes',
  accept: 'Accept filing',
  reject: 'Reject filing',
}

export function nextActions(status: FilingStatus, role: Role): string[] {
  return Object.entries(TRANSITIONS)
    .filter(([, [from, , r]]) => from === status && r === role)
    .map(([action]) => action)
}
