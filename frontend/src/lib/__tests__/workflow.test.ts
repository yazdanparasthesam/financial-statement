import { describe, expect, it } from 'vitest'
import { ACTION_LABELS, STATUS_META, nextActions } from '../workflow'
import type { FilingStatus } from '../../api/types'

const ALL_STATUSES: FilingStatus[] = ['draft', 'submitted', 'in_review', 'changes_requested', 'accepted', 'rejected']

describe('workflow mirror', () => {
  it('covers every backend status with UI metadata', () => {
    for (const s of ALL_STATUSES) {
      expect(STATUS_META[s]).toBeDefined()
      expect(STATUS_META[s].label.length).toBeGreaterThan(0)
      expect(STATUS_META[s].badge).toContain('bg-')
      expect(STATUS_META[s].desc.length).toBeGreaterThan(10)
    }
  })

  it('preparer in draft can only submit', () => {
    expect(nextActions('draft', 'preparer')).toEqual(['submit'])
  })

  it('reviewer in_review can accept/reject/request changes', () => {
    expect(nextActions('in_review', 'reviewer').sort()).toEqual(['accept', 'reject', 'request_changes'])
  })

  it('roles never see each other’s actions', () => {
    expect(nextActions('draft', 'reviewer')).toEqual([])
    expect(nextActions('submitted', 'preparer')).toEqual([])
    expect(nextActions('in_review', 'preparer')).toEqual([])
  })

  it('changes_requested loop: preparer reopens', () => {
    expect(nextActions('changes_requested', 'preparer')).toEqual(['reopen'])
  })

  it('terminal statuses have no actions', () => {
    expect(nextActions('accepted', 'preparer')).toEqual([])
    expect(nextActions('accepted', 'reviewer')).toEqual([])
    expect(nextActions('rejected', 'reviewer')).toEqual([])
  })

  it('every action has a human label', () => {
    const actions = ['submit', 'reopen', 'start_review', 'request_changes', 'accept', 'reject']
    for (const a of actions) expect(ACTION_LABELS[a]).toBeTruthy()
  })
})
