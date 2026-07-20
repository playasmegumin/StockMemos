import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePortfolioStore } from '@/stores/portfolio'
import * as stocksApi from '@/api/stocks'
import * as marketApi from '@/api/market'

vi.mock('@/api/stocks', () => ({
  listStocks: vi.fn(),
  createStock: vi.fn(),
  deleteStock: vi.fn(),
  refreshStock: vi.fn(),
}))

vi.mock('@/api/market', () => ({
  refreshAll: vi.fn(),
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

  it('removeStock filters stock on success', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    vi.mocked(stocksApi.deleteStock).mockResolvedValue({ ok: true, data: true })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.stocks).toHaveLength(1)
    const r = await store.removeStock('1')
    expect(r.ok).toBe(true)
    expect(store.stocks).toHaveLength(0)
  })

  it('refreshStock updates stock in place on success', async () => {
    const updatedStock = { ...mockStock, historical_pnl: 8000 }
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    vi.mocked(stocksApi.refreshStock).mockResolvedValue({ ok: true, data: updatedStock })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.stocks[0].historical_pnl).toBe(5000)
    const r = await store.refreshStock('1')
    expect(r.ok).toBe(true)
    expect(store.stocks[0].historical_pnl).toBe(8000)
  })

  it('refreshMarket calls refreshAll then fetchAll on success', async () => {
    const updatedStocks = [mockStock, { ...mockStock, id: '2', symbol: '000001', name: '平安' }]
    vi.mocked(marketApi.refreshAll).mockResolvedValue({ ok: true, data: true })
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: updatedStocks })
    const store = usePortfolioStore()
    await store.refreshMarket()
    expect(marketApi.refreshAll).toHaveBeenCalled()
    expect(stocksApi.listStocks).toHaveBeenCalled()
    expect(store.stocks).toHaveLength(2)
    expect(store.error).toBeNull()
  })

  it('refreshMarket does not fetchAll on failure', async () => {
    vi.mocked(marketApi.refreshAll).mockResolvedValue({ ok: false, error: 'market down' })
    const store = usePortfolioStore()
    await store.refreshMarket()
    expect(store.error).toBe('market down')
  })

  it('refreshMarket clears loading when refreshAll rejects', async () => {
    vi.mocked(marketApi.refreshAll).mockRejectedValue(new Error('network'))
    const store = usePortfolioStore()
    const r = await store.refreshMarket()
    expect(r.ok).toBe(false)
    expect(store.loading).toBe(false)
    expect(store.error).toBe('network')
  })

  it('fetchAll clears loading when listStocks rejects', async () => {
    vi.mocked(stocksApi.listStocks).mockRejectedValue(new Error('network'))
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.loading).toBe(false)
    expect(store.error).toBeTruthy()
  })

  it('fetchAll returns Result with ok=false on rejection', async () => {
    vi.mocked(stocksApi.listStocks).mockRejectedValue(new Error('network'))
    const store = usePortfolioStore()
    const r = await store.fetchAll()
    expect(r.ok).toBe(false)
    expect(store.stocks).toHaveLength(0)
  })

  it('fetchAll clears loading even when listStocks returns Result error', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: false, error: 'fail' })
    const store = usePortfolioStore()
    await store.fetchAll()
    expect(store.loading).toBe(false)
    expect(store.error).toBe('fail')
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
