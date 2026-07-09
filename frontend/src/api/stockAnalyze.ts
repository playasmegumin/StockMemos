import { wrapResult } from './client'
import type { Result } from '@/types/api'
import type { StockAnalyze, Report, TpSlPoint, StockTag } from '@/types/stockAnalyze'

// ── StockAnalyze ──

export function getAnalyze(stockId: string): Promise<Result<StockAnalyze>> {
  return wrapResult<StockAnalyze>({ method: 'GET', url: `/stock-analyze/stock/${stockId}` })
}

export function updateFundamentals(id: string, fundamentals_data: Record<string, any>): Promise<Result<StockAnalyze>> {
  return wrapResult<StockAnalyze>({ method: 'PUT', url: `/stock-analyze/${id}`, data: { fundamentals_data } })
}

// ── Reports ──

export function getReports(analyzeId: string): Promise<Result<Report[]>> {
  return wrapResult<Report[]>({ method: 'GET', url: `/stock-analyze/${analyzeId}/reports`, dedup: true })
}

export function createReport(analyzeId: string, data: { title: string; content: string; generated_at?: string }): Promise<Result<Report>> {
  return wrapResult<Report>({ method: 'POST', url: `/stock-analyze/${analyzeId}/reports`, data })
}

// ── TP/SL Points ──

export function getTpSlPoints(analyzeId: string): Promise<Result<TpSlPoint[]>> {
  return wrapResult<TpSlPoint[]>({ method: 'GET', url: `/stock-analyze/${analyzeId}/tp-sl-points`, dedup: true })
}

export function createTpSlPoint(analyzeId: string, data: { price: number; label: string; notes?: string }): Promise<Result<TpSlPoint>> {
  return wrapResult<TpSlPoint>({ method: 'POST', url: `/stock-analyze/${analyzeId}/tp-sl-points`, data })
}

export function deleteTpSlPoint(analyzeId: string, pointId: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/stock-analyze/${analyzeId}/tp-sl-points/${pointId}` })
}

// ── Tags ──

export function getTags(analyzeId: string): Promise<Result<StockTag[]>> {
  return wrapResult<StockTag[]>({ method: 'GET', url: `/stock-analyze/${analyzeId}/stock-tags`, dedup: true })
}

export function createTag(analyzeId: string, tag: string): Promise<Result<StockTag>> {
  return wrapResult<StockTag>({ method: 'POST', url: `/stock-analyze/${analyzeId}/stock-tags`, data: { tag } })
}

export function deleteTag(analyzeId: string, tagId: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/stock-analyze/${analyzeId}/stock-tags/${tagId}` })
}
