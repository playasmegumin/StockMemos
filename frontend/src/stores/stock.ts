import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Stock } from '@/types/stock'
import type { StockAnalyze, Report, TpSlPoint, StockTag } from '@/types/stockAnalyze'
import * as stocksApi from '@/api/stocks'
import * as analyzeApi from '@/api/stockAnalyze'
import { refreshAll as refreshMarketApi } from '@/api/market'

export const useStockStore = defineStore('stock', () => {
  const stock = ref<Stock | null>(null)
  const analyze = ref<StockAnalyze | null>(null)
  const reports = ref<Report[]>([])
  const tpSlPoints = ref<TpSlPoint[]>([])
  const tags = ref<StockTag[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchAll(stockId: string) {
    loading.value = true
    error.value = null

    const [stockR, analyzeR] = await Promise.all([
      stocksApi.getStock(stockId),
      analyzeApi.getAnalyze(stockId),
    ])

    if (stockR.ok) stock.value = stockR.data
    else error.value = stockR.error

    if (analyzeR.ok) {
      analyze.value = analyzeR.data
      const aid = analyzeR.data.id
      const [reportsR, tpSlR, tagsR] = await Promise.all([
        analyzeApi.getReports(aid),
        analyzeApi.getTpSlPoints(aid),
        analyzeApi.getTags(aid),
      ])
      if (reportsR.ok) reports.value = reportsR.data
      if (tpSlR.ok) tpSlPoints.value = tpSlR.data
      if (tagsR.ok) tags.value = tagsR.data
    }

    loading.value = false
  }

  async function refreshPrice() {
    if (!stock.value) return
    const r = await stocksApi.getStock(stock.value.id)
    if (r.ok) stock.value = r.data
  }

  async function refreshMarket() {
    const r = await refreshMarketApi()
    if (r.ok && stock.value) {
      await fetchAll(stock.value.id)
    }
    return r
  }

  async function addTag(tag: string) {
    if (!analyze.value) return { ok: false, error: 'No analyze' } as const
    const r = await analyzeApi.createTag(analyze.value.id, tag)
    if (r.ok) tags.value.unshift(r.data)
    return r
  }

  async function removeTag(tagId: string) {
    if (!analyze.value) return { ok: false, error: 'No analyze' } as const
    const r = await analyzeApi.deleteTag(analyze.value.id, tagId)
    if (r.ok) tags.value = tags.value.filter(t => t.id !== tagId)
    return r
  }

  async function addReport(data: { title: string; content: string; generated_at?: string }) {
    if (!analyze.value) return { ok: false, error: 'No analyze' } as const
    const r = await analyzeApi.createReport(analyze.value.id, data)
    if (r.ok) reports.value.unshift(r.data)
    return r
  }

  async function addTpSlPoint(data: { price: number; label: string; notes?: string }) {
    if (!analyze.value) return { ok: false, error: 'No analyze' } as const
    const r = await analyzeApi.createTpSlPoint(analyze.value.id, data)
    if (r.ok) tpSlPoints.value.push(r.data)
    return r
  }

  async function removeTpSlPoint(pointId: string) {
    if (!analyze.value) return { ok: false, error: 'No analyze' } as const
    const r = await analyzeApi.deleteTpSlPoint(analyze.value.id, pointId)
    if (r.ok) tpSlPoints.value = tpSlPoints.value.filter(p => p.id !== pointId)
    return r
  }

  function $reset() {
    stock.value = null
    analyze.value = null
    reports.value = []
    tpSlPoints.value = []
    tags.value = []
    loading.value = false
    error.value = null
  }

  return {
    stock, analyze, reports, tpSlPoints, tags, loading, error,
    fetchAll, refreshPrice, refreshMarket,
    addTag, removeTag, addReport, addTpSlPoint, removeTpSlPoint, $reset,
  }
})
