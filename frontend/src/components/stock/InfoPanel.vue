<template>
  <div class="info-panel bg-white rounded-lg shadow-sm p-4 space-y-5">
    <!-- Stock code/name header -->
    <div>
      <div class="text-3xl font-mono font-bold text-gray-800">{{ stock?.symbol }}</div>
      <div class="text-sm text-gray-500 mt-1">
        {{ stock?.exchange }} · {{ stock?.name }}
      </div>
    </div>

    <!-- Key metrics -->
    <div class="space-y-3">
      <div class="flex justify-between items-center">
        <span class="text-gray-500 text-sm">当前价</span>
        <span class="text-lg font-mono font-semibold">{{ fmtPrice(currentPrice, stock?.currency) }}</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-500 text-sm">持仓</span>
        <span class="font-mono">{{ stock?.position ?? '--' }} 股</span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-500 text-sm">盈亏</span>
        <span v-if="pnlResult" class="font-mono font-semibold" :class="pnlResult.cls">{{ pnlResult.text }}</span>
        <span v-else class="font-mono text-gray-400">--</span>
      </div>
    </div>

    <t-divider />

    <!-- Fundamentals -->
    <div>
      <div class="text-sm font-semibold text-gray-600 mb-2">基本面</div>
      <div v-if="fundamentals.length > 0" class="space-y-2">
        <div
          v-for="item in fundamentals"
          :key="item.label"
          class="flex justify-between items-center text-sm"
        >
          <span class="text-gray-500">{{ item.label }}</span>
          <span class="font-mono">{{ item.value }}</span>
        </div>
      </div>
      <div v-else class="text-sm text-gray-400 py-2">暂无基本面数据</div>
    </div>

    <t-divider />

    <!-- Tags -->
    <div>
      <div class="text-sm font-semibold text-gray-600 mb-2">标签</div>
      <div v-if="stockStore.tags.length > 0" class="flex flex-wrap gap-2 mb-3">
        <t-tag
          v-for="tag in stockStore.tags"
          :key="tag.id"
          closable
          theme="primary"
          variant="light"
          @close="handleRemoveTag(tag.id)"
        >
          {{ tag.tag }}
        </t-tag>
      </div>
      <div v-else class="text-sm text-gray-400 py-2">暂无标签</div>
      <t-input
        v-model="newTag"
        placeholder="输入标签后按回车添加"
        @enter="handleAddTag"
        clearable
        size="small"
      />
    </div>

    <t-divider />

    <!-- Data info -->
    <div>
      <div class="text-sm font-semibold text-gray-600 mb-2">数据</div>
      <div class="space-y-2 text-sm">
        <div class="flex justify-between">
          <span class="text-gray-500">数据源</span>
          <span class="font-mono">{{ dataSourceLabel }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">添加日期</span>
          <span class="font-mono">{{ fmtDate(stock?.created_at) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">交易次数</span>
          <span class="font-mono">{{ txCount }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500">已缓存K线</span>
          <span class="font-mono">{{ klineCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStockStore } from '@/stores/stock'
import { useKlineStore } from '@/stores/kline'
import { getPrice, getKline } from '@/api/market'
import { getTransactionsByStock } from '@/api/transactions'
import { fmtPrice, fmtPnl, fmtDecimal, fmtPercent, fmtAmount, fmtDate } from '@/utils/format'
import type { CurrentPrice } from '@/types/market'

const stockStore = useStockStore()
const klineStore = useKlineStore()

const stock = computed(() => stockStore.stock)
const newTag = ref('')
const currentPriceData = ref<CurrentPrice | null>(null)
const currentPrice = computed(() => currentPriceData.value?.price ?? null)
const txCount = ref(0)
const klineCount = computed(() => klineStore.klineData.length)

const dataSourceLabel = computed(() => {
  if (!stock.value) return '--'
  if (stock.value.exchange === 'SH' || stock.value.exchange === 'SZ') return 'TuShare'
  return 'YFinance'
})

const pnlResult = computed(() => {
  if (!stock.value) return null
  return fmtPnl(stock.value.historical_pnl)
})

// Fundamentals display config
const FUNDAMENTAL_KEYS: { key: string; label: string; format: (v: any) => string }[] = [
  { key: 'pe_ratio', label: 'PE (TTM)', format: fmtDecimal },
  { key: 'pb_ratio', label: 'PB', format: fmtDecimal },
  { key: 'roe', label: 'ROE', format: fmtPercent },
  { key: 'market_cap', label: '总市值', format: (v) => fmtAmount(v) },
  { key: 'dividend_yield', label: '股息率', format: fmtPercent },
  { key: 'profit_margin', label: '净利润率', format: fmtPercent },
  { key: 'debt_to_equity', label: '负债/权益比', format: fmtDecimal },
  { key: 'current_ratio', label: '流动比率', format: fmtDecimal },
  { key: 'eps', label: '每股收益 (EPS)', format: fmtDecimal },
  { key: 'industry', label: '行业', format: (v) => String(v) },
]

const fundamentals = computed(() => {
  const fd = stockStore.analyze?.fundamentals_data
  if (!fd) return []
  return FUNDAMENTAL_KEYS
    .filter(meta => fd[meta.key] != null)
    .map(meta => ({
      label: meta.label,
      value: meta.format(fd[meta.key]),
    }))
})

async function handleAddTag() {
  const val = newTag.value.trim()
  if (!val) return
  await stockStore.addTag(val)
  newTag.value = ''
}

function handleRemoveTag(tagId: string) {
  stockStore.removeTag(tagId)
}

onMounted(async () => {
  if (!stock.value) return
  const [priceR, txnR] = await Promise.all([
    getPrice(stock.value.id),
    getTransactionsByStock(stock.value.id),
  ])
  if (priceR.ok) {
    currentPriceData.value = priceR.data
  }
  if (txnR.ok && txnR.data) {
    txCount.value = txnR.data.length
  }
})
</script>
