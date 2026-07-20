import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Stock } from '@/types/stock'
import type { Result } from '@/types/api'
import * as stocksApi from '@/api/stocks'
import { refreshAll as refreshMarketApi } from '@/api/market'

export const usePortfolioStore = defineStore('portfolio', () => {
  const stocks = ref<Stock[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const stockCount = computed(() => stocks.value.length)
  const totalPosition = computed(() => stocks.value.reduce((s, st) => s + st.position, 0))
  const totalPnl = computed(() => stocks.value.reduce((s, st) => s + st.historical_pnl, 0))
  const profitableCount = computed(() => stocks.value.filter(s => s.historical_pnl > 0).length)

  async function fetchAll(): Promise<Result<Stock[]>> {
    loading.value = true
    error.value = null
    try {
      const r = await stocksApi.listStocks()
      if (r.ok) {
        stocks.value = r.data
      } else {
        error.value = r.error
      }
      return r
    } catch (err: any) {
      const msg = err?.message ?? '网络连接失败'
      error.value = msg
      return { ok: false, error: msg }
    } finally {
      loading.value = false
    }
  }

  async function addStock(data: { symbol: string; name?: string }) {
    const r = await stocksApi.createStock(data)
    if (r.ok) {
      stocks.value.push(r.data)
    }
    return r
  }

  async function removeStock(id: string) {
    const r = await stocksApi.deleteStock(id)
    if (r.ok) {
      stocks.value = stocks.value.filter(s => s.id !== id)
    }
    return r
  }

  async function refreshStock(id: string) {
    const r = await stocksApi.refreshStock(id)
    if (r.ok) {
      const idx = stocks.value.findIndex(s => s.id === id)
      if (idx !== -1) {
        stocks.value[idx] = r.data
      }
    }
    return r
  }

  async function refreshMarket() {
    loading.value = true
    error.value = null
    try {
      const r = await refreshMarketApi()
      if (r.ok) {
        await fetchAll()
      } else {
        error.value = r.error
      }
      return r
    } catch (err: any) {
      const msg = err?.message ?? '行情刷新失败'
      error.value = msg
      return { ok: false, error: msg } as const
    } finally {
      loading.value = false
    }
  }

  function $reset() {
    stocks.value = []
    loading.value = false
    error.value = null
  }

  return {
    stocks, loading, error,
    stockCount, totalPosition, totalPnl, profitableCount,
    fetchAll, addStock, removeStock, refreshStock, refreshMarket, $reset,
  }
})
