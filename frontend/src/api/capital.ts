import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface CapitalSummary {
  total_invested_cny: number
  total_historical_pnl_cny: number
  total_position_value_cny: number
  total_adjustment_cny: number
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

export type AdjustmentCurrency = 'CNY' | 'HKD' | 'USD'

export interface HistoricalAdjustment {
  id: string
  amount: number
  currency: AdjustmentCurrency
  note: string | null
  created_at: string | null
  updated_at: string | null
}

export interface AdjustmentPayload {
  amount: number
  currency: AdjustmentCurrency
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

export function listAdjustments(): Promise<Result<HistoricalAdjustment[]>> {
  return wrapResult<HistoricalAdjustment[]>({ method: 'GET', url: '/historical-adjustments' })
}

export function createAdjustment(data: AdjustmentPayload): Promise<Result<HistoricalAdjustment>> {
  return wrapResult<HistoricalAdjustment>({ method: 'POST', url: '/historical-adjustments', data })
}

export function updateAdjustment(
  id: string,
  data: AdjustmentPayload,
): Promise<Result<HistoricalAdjustment>> {
  return wrapResult<HistoricalAdjustment>({
    method: 'PUT',
    url: `/historical-adjustments/${id}`,
    data,
  })
}

export async function deleteAdjustment(id: string): Promise<Result<true>> {
  const result = await wrapResult<undefined>({ method: 'DELETE', url: `/historical-adjustments/${id}` })
  if (result.ok) {
    return { ok: true, data: true }
  }
  return result
}
