import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface CapitalSummary {
  total_invested_cny: number
  total_historical_pnl_cny: number
  total_position_value_cny: number
}

export interface CapitalFlow {
  id: string
  type: string
  amount: number
  currency: string
  note: string | null
  created_at: string | null
}

export interface CapitalFlowCreate {
  type: 'deposit' | 'withdraw' | 'fee'
  amount: number
  currency?: string
  note?: string
}

export function getCapitalSummary(): Promise<Result<CapitalSummary>> {
  return wrapResult<CapitalSummary>({ method: 'GET', url: '/capital/summary' })
}

export function listCapitalFlows(limit = 50, offset = 0): Promise<Result<CapitalFlow[]>> {
  return wrapResult<CapitalFlow[]>({
    method: 'GET',
    url: '/capital/flows',
    params: { limit, offset },
  })
}

export function createCapitalFlow(data: CapitalFlowCreate): Promise<Result<CapitalFlow>> {
  return wrapResult<CapitalFlow>({ method: 'POST', url: '/capital/flows', data })
}

export function deleteCapitalFlow(id: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/capital/flows/${id}` })
}
