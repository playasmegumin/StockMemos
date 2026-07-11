<template>
  <div>
    <div class="flex justify-between items-center mb-3">
      <span class="text-lg font-medium">持仓列表</span>
      <t-button @click="$emit('add-stock')">添加股票</t-button>
    </div>
    <t-table
      :data="sortedStocks"
      :columns="columns"
      row-key="id"
      :sort="sortState"
      @sort-change="onSortChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { Stock } from '@/types/stock'
import type { CurrentPrice } from '@/types/market'
import { getPrice } from '@/api/market'
import { fmtAmount, fmtPnl, fmtPrice } from '@/utils/format'

const props = defineProps<{
  stocks: Stock[]
}>()

const emit = defineEmits<{
  (e: 'delete-stock', id: string): void
  (e: 'add-stock'): void
  (e: 'refresh-stock', id: string): void
}>()

const router = useRouter()

// Sorting
const sortState = ref<{ sortBy: string; descending: boolean }>({ sortBy: '', descending: false })

const columns = computed(() => [
  {
    colKey: 'name',
    title: '名称',
    width: 160,
    cell: (_h: any, { row }: Record<string, any>) => {
      if (!row) return ''
      return h('a', {
        style: { color: '#1677ff', cursor: 'pointer', textDecoration: 'underline' },
        onClick: () => router.push(`/stock/${row.id}`),
      }, row.name)
    },
  },
  { colKey: 'symbol', title: '代码', width: 100, cell: (_h: any, { row }: Record<string, any>) => row ? row.symbol : '' },
  { colKey: 'exchange', title: '交易所', width: 90, cell: (_h: any, { row }: Record<string, any>) => row ? row.exchange : '' },
  {
    colKey: 'position', title: '持仓', width: 120, sortable: true,
    cell: (_h: any, { row }: Record<string, any>) => row ? fmtAmount(row.position) : '',
  },
  {
    colKey: 'historical_pnl', title: '盈亏', width: 140, sortable: true,
    cell: (_h: any, { row }: Record<string, any>) => {
      if (!row) return ''
      const { text, cls } = fmtPnl(row.historical_pnl)
      const color = cls.includes('red') ? '#e74c3c' : '#27ae60'
      return h('span', { style: `color:${color};font-weight:600` }, text)
    },
  },
  {
    colKey: 'price', title: '现价', width: 130,
    cell: (_h: any, { row }: Record<string, any>) => {
      if (!row) return ''
      if (priceLoading.value.get(row.id)) return '加载中...'
      const p = priceMap.value.get(row.id)
      return p ? fmtPrice(p.price) : '--'
    },
  },
  {
    colKey: 'tags', title: '标签', width: 180,
    cell: (_h: any, { row }: Record<string, any>) => {
      if (!row) return null
      const tags = (row as any).tags
      if (!tags?.length) return null
      return tags.slice(0, 3).join(', ') + (tags.length > 3 ? ` +${tags.length - 3}` : '')
    },
  },
  {
    colKey: 'actions', title: '操作', width: 200, align: 'center' as const,
    cell: (_h: any, { row }: Record<string, any>) => {
      if (!row) return null
      return h('div', { style: 'display:flex;gap:8px;justify-content:center' }, [
        h('a', {
          style: 'color:#1677ff;cursor:pointer',
          onClick: () => router.push(`/stock/${row.id}`),
        }, '详情'),
        h('a', {
          style: 'color:#1677ff;cursor:pointer',
          onClick: () => emit('refresh-stock', row.id),
        }, '重置'),
        h('a', {
          style: 'color:#e74c3c;cursor:pointer',
          onClick: () => emit('delete-stock', row.id),
        }, '删除'),
      ])
    },
  },
])

const sortedStocks = computed(() => {
  if (!sortState.value.sortBy) return props.stocks
  const arr = [...props.stocks]
  const key = sortState.value.sortBy as keyof Stock
  arr.sort((a, b) => {
    const aVal = Number(a[key]) || 0
    const bVal = Number(b[key]) || 0
    return sortState.value.descending ? bVal - aVal : aVal - bVal
  })
  return arr
})

function onSortChange(val: { sortBy: string; descending: boolean }) {
  sortState.value = { ...val }
}

// Price fetching
const priceMap = ref(new Map<string, CurrentPrice>())
const priceLoading = ref(new Map<string, boolean>())

watch(() => props.stocks?.length, async () => {
  const stocks = props.stocks
  if (!stocks || stocks.length === 0) return
  for (const stock of stocks) {
    if (priceMap.value.has(stock.id)) continue
    priceLoading.value.set(stock.id, true)
    const r = await getPrice(stock.id)
    if (r.ok) {
      priceMap.value.set(stock.id, r.data)
    }
    priceLoading.value.set(stock.id, false)
  }
}, { immediate: true })
</script>
