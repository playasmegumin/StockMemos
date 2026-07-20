import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import PortfolioDashboard from '@/pages/PortfolioDashboard.vue'
import * as stocksApi from '@/api/stocks'
import * as capitalApi from '@/api/capital'
import * as marketApi from '@/api/market'

// ── API mocks ──
vi.mock('@/api/stocks', () => ({
  listStocks: vi.fn(),
  createStock: vi.fn(),
  deleteStock: vi.fn(),
  refreshStock: vi.fn(),
}))

vi.mock('@/api/capital', () => ({
  getCapitalSummary: vi.fn(),
}))

vi.mock('@/api/market', () => ({
  refreshAll: vi.fn(),
}))

// ── TDesign stub (prevents SVG icon resolution errors) ──
vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: { success: vi.fn(), warning: vi.fn() },
}))

const mockStock = {
  id: '1', exchange: 'SH', symbol: '600519', name: '茅台',
  currency: 'CNY', position: 100, historical_pnl: 5000,
  created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z',
}

const mockCapitalSummary = {
  total_invested_cny: 100000,
  total_historical_pnl_cny: 20000,
  total_position_value_cny: 120000,
  total_adjustment_cny: 0,
}

beforeEach(() => {
  setActivePinia(createPinia())
})

function mountDashboard() {
  // Stub all child components to avoid complex dependency chains
  return mount(PortfolioDashboard, {
    global: {
      stubs: {
        't-button': { template: '<button><slot /></button>' },
        't-icon': { template: '<span />' },
        't-alert': { template: '<div><slot /><slot name="operations" /></div>' },
        't-dialog': {
          props: ['visible', 'header', 'body', 'confirmBtn', 'cancelBtn'],
          template: '<div v-if="visible"><slot /><slot name="actions" /></div>',
        },
        't-form': { template: '<div><slot /></div>' },
        't-form-item': { template: '<div><slot /></div>' },
        't-input': { template: '<input />' },
        KpiCards: { template: '<div class="kpi-cards" />' },
        PortfolioTreemap: {
          props: ['stocks', 'refreshTrigger'],
          template: '<div class="treemap-stub" :data-trigger="refreshTrigger" />',
        },
        StockTable: { template: '<div class="stock-table" />' },
      },
    },
  })
}

function flush() {
  return new Promise(resolve => setTimeout(resolve, 0))
}

describe('PortfolioDashboard refresh lane', () => {
  it('onMounted bumps treemap refresh trigger after fetch completes', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: mockCapitalSummary })

    const wrapper = mountDashboard()
    await flush()

    // After mount, loadDashboardData runs, fetchAll returns → trigger is bumped once
    expect(wrapper.vm.treemapRefreshTrigger).toBe(1)
    expect(stocksApi.listStocks).toHaveBeenCalledTimes(1)
  })

  it('refresh handler bumps treemap refresh trigger again', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: mockCapitalSummary })
    vi.mocked(marketApi.refreshAll).mockResolvedValue({ ok: true, data: true })

    const wrapper = mountDashboard()
    await flush()

    // Trigger a market refresh
    await wrapper.vm.loadDashboardData()
    await flush()

    // Each loadDashboardData bumps trigger
    expect(wrapper.vm.treemapRefreshTrigger).toBe(2)
  })

  it('same stock count with changed positions still bumps trigger', async () => {
    // Initial stock list
    vi.mocked(stocksApi.listStocks).mockResolvedValueOnce({ ok: true, data: [mockStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: mockCapitalSummary })

    const wrapper = mountDashboard()
    await flush()
    expect(wrapper.vm.treemapRefreshTrigger).toBe(1)

    // Update mocked list: same count, changed position
    const updatedStock = { ...mockStock, position: 200, historical_pnl: 8000 }
    vi.mocked(stocksApi.listStocks).mockResolvedValueOnce({ ok: true, data: [updatedStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValueOnce({ ok: true, data: mockCapitalSummary })

    // Simulate a mutation → loadDashboardData is called
    await wrapper.vm.loadDashboardData()
    await flush()

    expect(wrapper.vm.treemapRefreshTrigger).toBe(2)
    // Verify the store actually has the updated data
    const storeStocks = (await import('@/stores/portfolio')).usePortfolioStore()
    expect(storeStocks.stocks[0].position).toBe(200)
  })

  it('handleRefresh clears refreshing when market API rejects', async () => {
    vi.mocked(stocksApi.listStocks).mockResolvedValue({ ok: true, data: [mockStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: mockCapitalSummary })
    vi.mocked(marketApi.refreshAll).mockRejectedValue(new Error('network'))

    const wrapper = mountDashboard()
    await flush()

    // refreshing must be false initially
    expect(wrapper.vm.refreshing).toBe(false)

    await expect(wrapper.vm.handleRefresh()).resolves.toBeUndefined()

    const store = (await import('@/stores/portfolio')).usePortfolioStore()
    expect(wrapper.vm.refreshing).toBe(false)
    expect(store.loading).toBe(false)
    expect(store.error).toBe('network')
  })

  it('failed stock-list refresh does not bump treemap trigger', async () => {
    // Mount: listStocks succeeds → trigger bumped to 1
    vi.mocked(stocksApi.listStocks).mockResolvedValueOnce({ ok: true, data: [mockStock] })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: mockCapitalSummary })

    const wrapper = mountDashboard()
    await flush()
    expect(wrapper.vm.treemapRefreshTrigger).toBe(1)

    // Now simulate a loadDashboardData where fetchAll returns Result.ok=false
    vi.mocked(stocksApi.listStocks).mockResolvedValueOnce({ ok: false, error: 'API error' })
    vi.mocked(capitalApi.getCapitalSummary).mockResolvedValueOnce({ ok: true, data: mockCapitalSummary })

    await wrapper.vm.loadDashboardData()
    await flush()

    // Trigger must NOT have been bumped — stock list refresh failed
    expect(wrapper.vm.treemapRefreshTrigger).toBe(1)
  })
})
