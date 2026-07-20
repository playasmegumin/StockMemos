import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useStockStore } from '@/stores/stock'
import StockDetail from '@/pages/StockDetail.vue'
import type { Stock } from '@/types/stock'
import type { StockAnalyze } from '@/types/stockAnalyze'

// ── Router mock ────────────────────────────────────────────────────
vi.mock('vue-router', () => ({
  useRoute: vi.fn(() => ({ params: { id: 'stock-1' } })),
  useRouter: vi.fn(() => ({ push: vi.fn() })),
}))

// ── API mocks ──────────────────────────────────────────────────────
vi.mock('@/api/stocks', () => ({
  getStock: vi.fn(),
}))

vi.mock('@/api/stockAnalyze', () => ({
  getAnalyze: vi.fn(),
  getReports: vi.fn(),
  getTpSlPoints: vi.fn(),
  getTags: vi.fn(),
  createTag: vi.fn(),
  deleteTag: vi.fn(),
}))

vi.mock('@/api/transactions', () => ({
  getTransactionsByStock: vi.fn(),
  deleteTransaction: vi.fn(),
}))

vi.mock('@/api/market', () => ({
  getPrice: vi.fn(),
  getKline: vi.fn(),
}))

// ── TDesign plugin mock ────────────────────────────────────────────
vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  DialogPlugin: vi.fn(() => ({ hide: vi.fn() })),
}))

// ── Fixtures ───────────────────────────────────────────────────────
const mockStock: Stock = {
  id: 'stock-1',
  exchange: 'SH',
  symbol: '600519',
  name: '茅台',
  currency: 'CNY',
  position: 200,
  historical_pnl: 50000,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-15T00:00:00Z',
}

const mockAnalyze: StockAnalyze = {
  id: 'analyze-1',
  stock_id: 'stock-1',
  fundamentals_data: null,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-15T00:00:00Z',
}

beforeEach(() => {
  setActivePinia(createPinia())
})

// ── Shared stubs for globally-registered TDesign components ────────
// Wrapper components (t-tab-panel, t-loading, t-alert) must render
// their default slots so child components like TransactionList appear.
const tdesignStubs = {
  't-link': true,
  't-button': true,
  't-tabs': { template: '<div><slot /></div>' },
  't-tab-panel': { template: '<div><slot /></div>' },
  't-loading': { template: '<div><slot /></div>' },
  't-alert': { template: '<div><slot /></div>' },
}

function mountDetail(stubs?: Record<string, any>) {
  return shallowMount(StockDetail, {
    global: {
      stubs: { ...tdesignStubs, ...stubs },
    },
  })
}

// ── Tests ──────────────────────────────────────────────────────────
describe('StockDetail responds to TransactionList changed', () => {
  it('calls refreshPrice and InfoPanel.refresh when TransactionList emits changed', async () => {
    // Arrange: mock all API calls that onMounted(loadData) triggers
    const { getStock } = await import('@/api/stocks')
    const { getAnalyze, getReports, getTpSlPoints, getTags } = await import('@/api/stockAnalyze')
    const { getKline } = await import('@/api/market')
    const { getTransactionsByStock } = await import('@/api/transactions')

    vi.mocked(getStock).mockResolvedValue({ ok: true, data: mockStock })
    vi.mocked(getAnalyze).mockResolvedValue({ ok: true, data: mockAnalyze })
    vi.mocked(getReports).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTpSlPoints).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTags).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getKline).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [] })

    const infoPanelRefresh = vi.fn()
    const wrapper = mountDetail({
      InfoPanel: {
        name: 'InfoPanel',
        setup: () => ({ refresh: infoPanelRefresh }),
        template: '<div class="mock-info-panel" />',
      },
    })

    // Wait for onMounted loadData to finish
    await new Promise(process.nextTick)
    await new Promise(process.nextTick)

    // Spy on refreshPrice AFTER mount so we don't count the initial load
    const store = useStockStore()
    const refreshSpy = vi.spyOn(store, 'refreshPrice')
    vi.mocked(getStock).mockClear()
    vi.mocked(getStock).mockResolvedValue({ ok: true, data: { ...mockStock, position: 300 } })

    // Act: emit changed from the TransactionList stub
    const txList = wrapper.findComponent({ name: 'TransactionList' })
    expect(txList.exists()).toBe(true)
    await txList.vm.$emit('changed')

    // Flush pending async work
    await new Promise(process.nextTick)

    // Assert: both the store and InfoPanel were refreshed
    expect(refreshSpy).toHaveBeenCalledTimes(1)
    expect(vi.mocked(getStock)).toHaveBeenCalledWith('stock-1')
    expect(infoPanelRefresh).toHaveBeenCalled()
  })

  it('updates stock store position after refreshPrice completes', async () => {
    const { getStock } = await import('@/api/stocks')
    const { getAnalyze, getReports, getTpSlPoints, getTags } = await import('@/api/stockAnalyze')
    const { getKline } = await import('@/api/market')
    const { getTransactionsByStock } = await import('@/api/transactions')

    vi.mocked(getStock).mockResolvedValue({ ok: true, data: mockStock })
    vi.mocked(getAnalyze).mockResolvedValue({ ok: true, data: mockAnalyze })
    vi.mocked(getReports).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTpSlPoints).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTags).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getKline).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [] })

    const wrapper = mountDetail()
    await new Promise(process.nextTick)
    await new Promise(process.nextTick)

    const store = useStockStore()
    expect(store.stock?.position).toBe(200)

    vi.mocked(getStock).mockResolvedValue({
      ok: true,
      data: { ...mockStock, position: 300, historical_pnl: 60000 },
    })

    const txList = wrapper.findComponent({ name: 'TransactionList' })
    await txList.vm.$emit('changed')
    await new Promise(process.nextTick)

    expect(store.stock?.position).toBe(300)
    expect(store.stock?.historical_pnl).toBe(60000)
  })

  it('preserves analyze and reports data after refreshPrice (no unnecessary reload)', async () => {
    const { getStock } = await import('@/api/stocks')
    const { getAnalyze, getReports, getTpSlPoints, getTags } = await import('@/api/stockAnalyze')
    const { getKline } = await import('@/api/market')
    const { getTransactionsByStock } = await import('@/api/transactions')

    vi.mocked(getStock).mockResolvedValue({ ok: true, data: mockStock })
    vi.mocked(getAnalyze).mockResolvedValue({
      ok: true,
      data: mockAnalyze,
    })
    vi.mocked(getReports).mockResolvedValue({
      ok: true,
      data: [{ id: 'r-1', stock_analyze_id: 'analyze-1', generated_at: '2025-01-10', title: 'Report', content: '...', created_at: '' }],
    })
    vi.mocked(getTpSlPoints).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTags).mockResolvedValue({
      ok: true,
      data: [{ id: 't-1', stock_analyze_id: 'analyze-1', tag: '白酒', created_at: '' }],
    })
    vi.mocked(getKline).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [] })

    const wrapper = mountDetail()
    await new Promise(process.nextTick)
    await new Promise(process.nextTick)

    const store = useStockStore()
    expect(store.reports).toHaveLength(1)
    expect(store.tags).toHaveLength(1)

    vi.mocked(getStock).mockResolvedValue({ ok: true, data: { ...mockStock, position: 300 } })

    const txList = wrapper.findComponent({ name: 'TransactionList' })
    await txList.vm.$emit('changed')
    await new Promise(process.nextTick)

    // Analyze/reports/tags must survive — refreshPrice does not touch them
    expect(store.reports).toHaveLength(1)
    expect(store.tags).toHaveLength(1)
    expect(store.analyze).toEqual(mockAnalyze)
    // Stock position updated
    expect(store.stock?.position).toBe(300)
  })
})
