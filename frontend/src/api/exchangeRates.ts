import { wrapResult } from './client'
import type { Result } from '@/types/api'

export interface ExchangeRateItem {
  currency: string
  rate_to_cny: number
  updated_at: string | null
}

export function listExchangeRates(): Promise<Result<ExchangeRateItem[]>> {
  return wrapResult<ExchangeRateItem[]>({ method: 'GET', url: '/capital/exchange-rates' })
}

export function updateExchangeRate(currency: string, rate_to_cny: number): Promise<Result<ExchangeRateItem>> {
  return wrapResult<ExchangeRateItem>({
    method: 'PUT',
    url: `/capital/exchange-rates/${currency}`,
    data: { rate_to_cny },
  })
}
