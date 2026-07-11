import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Stock } from '@/types/stock'
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

  async function fetchAll() {
    loading.value = true
    error.value = null
    const r = await stocksApi.listStocks()
    if (r.ok) {
      stocks.value = r.data
    } else {
      error.value = r.error
    }
    loading.value = false
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

  async function refreshMarket() {
    loading.value = true
    const r = await refreshMarketApi()
    if (r.ok) {
      await fetchAll()
    } else {
      error.value = r.error
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
    fetchAll, addStock, removeStock, refreshMarket, $reset,
  }
})
