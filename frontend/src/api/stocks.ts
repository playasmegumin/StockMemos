import { wrapResult } from './client'
import type { Result } from '@/types/api'
import type { Stock, StockCreate, StockUpdate } from '@/types/stock'

export function listStocks(): Promise<Result<Stock[]>> {
  return wrapResult<Stock[]>({ method: 'GET', url: '/stocks', dedup: true })
}

export function getStock(id: string): Promise<Result<Stock>> {
  return wrapResult<Stock>({ method: 'GET', url: `/stocks/${id}` })
}

export function createStock(data: StockCreate): Promise<Result<Stock>> {
  return wrapResult<Stock>({ method: 'POST', url: '/stocks', data })
}

export function updateStock(id: string, data: StockUpdate): Promise<Result<Stock>> {
  return wrapResult<Stock>({ method: 'PUT', url: `/stocks/${id}`, data })
}

export function deleteStock(id: string): Promise<Result<true>> {
  return wrapResult<true>({ method: 'DELETE', url: `/stocks/${id}` })
}
