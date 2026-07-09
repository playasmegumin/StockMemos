import { wrapResult } from './client'
import type { Result } from '@/types/api'
import type { CurrentPrice, DailyKline } from '@/types/market'

export function getPrice(stockId: string): Promise<Result<CurrentPrice>> {
  return wrapResult<CurrentPrice>({ method: 'GET', url: `/stocks/${stockId}/price`, dedup: true })
}

export function getKline(stockId: string, start?: string, end?: string): Promise<Result<DailyKline[]>> {
  return wrapResult<DailyKline[]>({
    method: 'GET',
    url: `/stocks/${stockId}/kline`,
    params: { start, end },
    dedup: true,
  })
}

export function refreshAll(): Promise<Result<true>> {
  return wrapResult<true>({ method: 'POST', url: '/market/refresh' })
}

export function refreshFundamentals(): Promise<Result<true>> {
  return wrapResult<true>({ method: 'POST', url: '/market/refresh-fundamentals' })
}
