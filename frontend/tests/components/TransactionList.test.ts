import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { useStockStore } from '@/stores/stock'
import TransactionList from '@/components/stock/TransactionList.vue'
import type { Stock } from '@/types/stock'
import type { StockAnalyze } from '@/types/stockAnalyze'

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

// ── TDesign plugin mock (programmatic APIs) ───────────────────────
const onConfirmRef: { current: (() => Promise<void>) | null } = { current: null }
vi.mock('tdesign-vue-next', () => ({
  MessagePlugin: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  DialogPlugin: vi.fn((config: any) => {
    onConfirmRef.current = config.onConfirm
    return { hide: vi.fn() }
  }),
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

const mockRow = {
  id: 'tx-1',
  stock_id: 'stock-1',
  quantity: 100,
  price: 1500,
  gas: 5,
  traded_at: '2025-01-10',
  created_at: '2025-01-10',
}

beforeEach(() => {
  setActivePinia(createPinia())
  onConfirmRef.current = null
})

// ── Shared stubs for globally-registered TDesign components ────────
const tdesignStubs = {
  't-button': true,
  't-link': true,
  't-space': true,
  't-table': true,
}

function mountWithStubs() {
  return shallowMount(TransactionList, {
    global: { stubs: tdesignStubs },
  })
}

// ── Tests ──────────────────────────────────────────────────────────
describe('TransactionList changed event', () => {
  it('emits changed after handleSaved (editor save flow)', async () => {
    const store = useStockStore()
    store.stock = { ...mockStock }
    store.analyze = { ...mockAnalyze }

    const { getTransactionsByStock } = await import('@/api/transactions')
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [mockRow] })

    const wrapper = mountWithStubs()

    // Call the same handler that runs after TransactionEditor emits @saved
    await wrapper.vm.handleSaved()

    const emitted = wrapper.emitted('changed')
    expect(emitted).toBeTruthy()
    expect(emitted).toHaveLength(1)
  })

  it('emits changed after delete flow (dialog confirm)', async () => {
    const store = useStockStore()
    store.stock = { ...mockStock }
    store.analyze = { ...mockAnalyze }

    const { getTransactionsByStock, deleteTransaction } = await import('@/api/transactions')
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(deleteTransaction).mockResolvedValue({ ok: true, data: true })

    const wrapper = mountWithStubs()

    // Invoke handleDelete — this calls DialogPlugin and registers onConfirm
    wrapper.vm.handleDelete(mockRow)
    expect(onConfirmRef.current).toBeInstanceOf(Function)

    // Execute the captured confirm callback — this drives the delete flow
    await onConfirmRef.current!()

    expect(vi.mocked(deleteTransaction)).toHaveBeenCalledWith('tx-1')
    const emitted = wrapper.emitted('changed')
    expect(emitted).toBeTruthy()
    expect(emitted).toHaveLength(1)
  })

  it('does not emit changed when delete API fails', async () => {
    const store = useStockStore()
    store.stock = { ...mockStock }
    store.analyze = { ...mockAnalyze }

    const { getTransactionsByStock, deleteTransaction } = await import('@/api/transactions')
    vi.mocked(getTransactionsByStock).mockResolvedValue({ ok: true, data: [] })
    vi.mocked(deleteTransaction).mockResolvedValue({ ok: false, error: 'fail' })

    const wrapper = mountWithStubs()

    wrapper.vm.handleDelete(mockRow)
    await onConfirmRef.current!()

    expect(wrapper.emitted('changed')).toBeFalsy()
  })
})
