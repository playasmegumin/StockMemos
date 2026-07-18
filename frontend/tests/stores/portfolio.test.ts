import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePortfolioStore } from '@/stores/portfolio'
import * as stocksApi from '@/api/stocks'

vi.mock('@/api/stocks', () => ({
  listStocks: vi.fn(),
  createStock: vi.fn(),
  deleteStock: vi.fn(),
}))

const mockStock = {
  id: '1', exchange: 'SH', symbol: '600519', name: '茅台',
  currency: 'CNY', position: 100, historical_pnl: 5000,
  created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z',
}

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('portfolio store', () => {
  it('fetchAll sets stocks on success', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.stocks).toHaveLength(1)
    expect(store.stockCount).toBe(1)
    expect(store.totalPosition).toBe(100)
    expect(store.totalPnl).toBe(5000)
  })

  it('fetchAll sets error on failure', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: false, error: 'fail' })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.stocks).toHaveLength(0)
    expect(store.error).toBe('fail')
  })

  it('addStock appends stock on success', async () => {
    vi.mocked(stocksApi.createStock).mockResolvedValue({ ok: true, data: mockStock })
    const store = usePortfolioStore()
    await store.addStock({ symbol: '600519', name: '茅台' })
    expect(store.stocks).toHaveLength(1)
  })

  it('$reset clears state', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.stocks).toHaveLength(1)
    store.$reset()
    expect(store.stocks).toHaveLength(0)
    expect(store.loading).toBe(false)
  })
})
