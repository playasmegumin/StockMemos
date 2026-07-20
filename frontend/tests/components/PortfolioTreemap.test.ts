import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import PortfolioTreemap from '@/components/dashboard/PortfolioTreemap.vue'
import type { Stock } from '@/types/stock'

// ── Mock every external dependency PortfolioTreemap touches ──

vi.mock('@/api/market', () => ({
  getPrice: vi.fn(),
  getKline: vi.fn(),
}))

vi.mock('@/api/transactions', () => ({
  getTransactionsByStock: vi.fn(),
}))

vi.mock('@/api/stockAnalyze', () => ({
  getAnalyze: vi.fn(),
  getTags: vi.fn(),
}))

vi.mock('@/config/exchangeRates', () => ({
  toCNY: vi.fn(() => 1),
}))

vi.mock('@/utils/positionValue', () => ({
  computeAllPositionValues: vi.fn(),
}))

// ECharts / vue-echarts: nothing to render in tests
vi.mock('echarts/core', () => ({ use: vi.fn() }))
vi.mock('vue-echarts', () => ({
  default: { template: '<div />', methods: { resize: vi.fn() } },
}))

const mockStock: Stock = {
  id: '1', exchange: 'SH', symbol: '600519', name: '茅台',
  currency: 'CNY', position: 100, historical_pnl: 5000,
  created_at: '2025-01-01T00:00:00Z', updated_at: '2025-01-01T00:00:00Z',
}

const mockPositionValue = { value: 120000, price: 1200, source: 'current' as const, currency: 'CNY', rate: 1 }

beforeEach(() => {
  vi.clearAllMocks()
})

function mountTreemap(stocks: Stock[], refreshTrigger = 0) {
  return mount(PortfolioTreemap, {
    props: { stocks, refreshTrigger },
    global: {
      stubs: {
        't-empty': { template: '<div class="t-empty" />' },
        't-loading': { template: '<div class="t-loading" />' },
      },
    },
  })
}

describe('PortfolioTreemap refresh trigger', () => {
  it('watches refreshTrigger prop — incrementing it calls loadData again', async () => {
    const { computeAllPositionValues } = await import('@/utils/positionValue')
    vi.mocked(computeAllPositionValues).mockResolvedValue(
      new Map([['1', mockPositionValue]]),
    )
    const { getAnalyze } = await import('@/api/stockAnalyze')
    vi.mocked(getAnalyze).mockResolvedValue({ ok: false, error: 'no analyze' })

    const wrapper = mountTreemap([mockStock], 1)
    await nextTick()
    await nextTick()
    await nextTick()

    // After mount, loadData should have been called once
    expect(computeAllPositionValues).toHaveBeenCalledTimes(1)

    // Now increment refreshTrigger to trigger another loadData
    await wrapper.setProps({ refreshTrigger: 2 })
    await nextTick()
    await nextTick()
    await nextTick()

    // computeAllPositionValues should have been called again after the trigger bump
    expect(computeAllPositionValues).toHaveBeenCalledTimes(2)
  })

  it('loadData sets loading false even when computeAllPositionValues rejects', async () => {
    const { computeAllPositionValues } = await import('@/utils/positionValue')
    vi.mocked(computeAllPositionValues).mockRejectedValue(new Error('API fail'))

    const wrapper = mountTreemap([mockStock], 0)
    // Give all async effects time to complete
    for (let i = 0; i < 5; i++) await nextTick()

    // loading must be false after the failed loadData completes
    expect(wrapper.vm.loading).toBe(false)
  })

  it('loadData preserves existing positionValues on failure', async () => {
    const { computeAllPositionValues } = await import('@/utils/positionValue')

    // First call — succeeds
    vi.mocked(computeAllPositionValues).mockResolvedValueOnce(
      new Map([['1', mockPositionValue]]),
    )

    const wrapper = mountTreemap([mockStock], 0)
    for (let i = 0; i < 5; i++) await nextTick()

    // Data was loaded successfully
    expect(wrapper.vm.positionValues.size).toBe(1)
    expect(wrapper.vm.positionValues.get('1')?.value).toBe(120000)
    expect(wrapper.vm.loading).toBe(false)

    // Second call — fails
    vi.mocked(computeAllPositionValues).mockRejectedValueOnce(new Error('API fail'))
    await wrapper.setProps({ refreshTrigger: 1 })
    for (let i = 0; i < 5; i++) await nextTick()

    // loading is false
    expect(wrapper.vm.loading).toBe(false)
    // previous positionValues should still be intact (was never reassigned)
    expect(wrapper.vm.positionValues.size).toBe(1)
    expect(wrapper.vm.positionValues.get('1')?.value).toBe(120000)
  })
})
