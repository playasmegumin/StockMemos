import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DailyKline } from '@/types/market'
import * as marketApi from '@/api/market'

export const useKlineStore = defineStore('kline', () => {
  const klineData = ref<DailyKline[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchKline(stockId: string) {
    loading.value = true
    error.value = null
    const r = await marketApi.getKline(stockId)
    if (r.ok) {
      klineData.value = r.data
    } else {
      error.value = r.error
    }
    loading.value = false
  }

  function $reset() {
    klineData.value = []
    loading.value = false
    error.value = null
  }

  return { klineData, loading, error, fetchKline, $reset }
})
