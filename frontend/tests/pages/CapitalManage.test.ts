import { beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import CapitalManage from '@/pages/CapitalManage.vue'
import * as capitalApi from '@/api/capital'
import type { HistoricalAdjustment } from '@/api/capital'

vi.mock('@/api/capital', () => ({
  getCapitalSummary: vi.fn(),
  listCapitalFlows: vi.fn(),
  createCapitalFlow: vi.fn(),
  deleteCapitalFlow: vi.fn(),
  listAdjustments: vi.fn(),
  createAdjustment: vi.fn(),
  updateAdjustment: vi.fn(),
  deleteAdjustment: vi.fn(),
}))

vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: { success: vi.fn(), warning: vi.fn() },
  DialogPlugin: vi.fn(() => ({ hide: vi.fn() })),
}))

const summary = {
  total_invested_cny: 0,
  total_historical_pnl_cny: 0,
  total_position_value_cny: 0,
  total_adjustment_cny: 0,
}

const adjustment: HistoricalAdjustment = {
  id: 'adj-1',
  amount: -250,
  currency: 'USD',
  note: 'legacy correction',
  created_at: '2026-07-01T00:00:00Z',
  updated_at: '2026-07-01T00:00:00Z',
}

function mountPage() {
  const wrapper = shallowMount(CapitalManage, {
    global: {
      stubs: {
        't-button': true,
        't-icon': true,
        't-table': true,
        't-space': true,
        't-link': true,
        't-tag': true,
        't-dialog': true,
        't-form': true,
        't-form-item': true,
        't-radio-group': true,
        't-radio': true,
        't-input-number': true,
        't-select': true,
        't-textarea': true,
      },
    },
  })
  return wrapper as typeof wrapper & {
    vm: {
      adjustmentForm: { amount: number; currency: 'CNY' | 'HKD' | 'USD'; note: string }
      openAddAdjustment: () => void
      openEditAdjustment: (row: HistoricalAdjustment) => void
      resetAdjustmentForm: () => void
      handleSaveAdjustment: () => Promise<void>
    }
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(capitalApi.getCapitalSummary).mockResolvedValue({ ok: true, data: summary })
  vi.mocked(capitalApi.listCapitalFlows).mockResolvedValue({ ok: true, data: [] })
  vi.mocked(capitalApi.listAdjustments).mockResolvedValue({ ok: true, data: [] })
  vi.mocked(capitalApi.createAdjustment).mockResolvedValue({ ok: true, data: adjustment })
  vi.mocked(capitalApi.updateAdjustment).mockResolvedValue({ ok: true, data: adjustment })
})

describe('CapitalManage adjustment currency', () => {
  it('defaults add currency to CNY and restores it on reset', () => {
    const wrapper = mountPage()

    wrapper.vm.openAddAdjustment()
    expect(wrapper.vm.adjustmentForm.currency).toBe('CNY')

    wrapper.vm.adjustmentForm.currency = 'HKD'
    wrapper.vm.resetAdjustmentForm()
    expect(wrapper.vm.adjustmentForm.currency).toBe('CNY')
  })

  it('preselects the record currency for editing', () => {
    const wrapper = mountPage()

    wrapper.vm.openEditAdjustment(adjustment)

    expect(wrapper.vm.adjustmentForm.currency).toBe('USD')
    expect(wrapper.vm.adjustmentForm.amount).toBe(-250)
  })

  it('includes currency in create and update payloads', async () => {
    const wrapper = mountPage()

    wrapper.vm.openAddAdjustment()
    wrapper.vm.adjustmentForm.amount = 100
    wrapper.vm.adjustmentForm.currency = 'HKD'
    await wrapper.vm.handleSaveAdjustment()
    expect(capitalApi.createAdjustment).toHaveBeenCalledWith({
      amount: 100,
      currency: 'HKD',
      note: undefined,
    })

    wrapper.vm.openEditAdjustment(adjustment)
    wrapper.vm.adjustmentForm.currency = 'CNY'
    await wrapper.vm.handleSaveAdjustment()
    expect(capitalApi.updateAdjustment).toHaveBeenCalledWith('adj-1', {
      amount: -250,
      currency: 'CNY',
      note: 'legacy correction',
    })
  })
})
