import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface InvestmentMemo {
  id: string
  title: string
  content: string
  stock_id: string | null
  created_at: string | null
  updated_at: string | null
}

export interface InvestmentMemoListItem {
  id: string
  title: string
  stock_id: string | null
  created_at: string | null
  updated_at: string | null
}

export interface InvestmentMemoCreate {
  title: string
  content: string
  stock_id?: string | null
}

export interface InvestmentMemoUpdate {
  title?: string
  content?: string
  stock_id?: string | null
}

export function listMemos(stockId?: string): Promise<Result<InvestmentMemoListItem[]>> {
  return wrapResult<InvestmentMemoListItem[]>({
    method: 'GET',
    url: '/memos',
    params: stockId ? { stock_id: stockId } : {},
  })
}

export function getMemo(id: string): Promise<Result<InvestmentMemo>> {
  return wrapResult<InvestmentMemo>({ method: 'GET', url: `/memos/${id}` })
}

export function createMemo(data: InvestmentMemoCreate): Promise<Result<InvestmentMemo>> {
  return wrapResult<InvestmentMemo>({ method: 'POST', url: '/memos', data })
}

export function updateMemo(id: string, data: InvestmentMemoUpdate): Promise<Result<InvestmentMemo>> {
  return wrapResult<InvestmentMemo>({ method: 'PUT', url: `/memos/${id}`, data })
}

export function deleteMemo(id: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/memos/${id}` })
}
