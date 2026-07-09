<template>
  <t-row :gutter="[16, 16]" class="mb-4">
    <t-col :span="6" :md="3">
      <t-card>
        <template #title>
          <div class="text-sm text-gray-500">股票数量</div>
        </template>
        <div class="text-2xl font-bold">{{ stockCount }}</div>
      </t-card>
    </t-col>
    <t-col :span="6" :md="3">
      <t-card>
        <template #title>
          <div class="text-sm text-gray-500">总持仓</div>
        </template>
        <div class="text-2xl font-bold">{{ fmtAmount(totalPosition) }}</div>
      </t-card>
    </t-col>
    <t-col :span="6" :md="3">
      <t-card>
        <template #title>
          <div class="text-sm text-gray-500">总盈亏</div>
        </template>
        <div :class="['text-2xl font-bold', totalPnl >= 0 ? 'text-red-600' : 'text-green-600']">
          {{ fmtPnl(totalPnl).text }}
        </div>
      </t-card>
    </t-col>
    <t-col :span="6" :md="3">
      <t-card>
        <template #title>
          <div class="text-sm text-gray-500">盈利股票</div>
        </template>
        <div class="text-2xl font-bold">{{ profitableCount }}</div>
      </t-card>
    </t-col>
  </t-row>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Stock } from '@/types/stock'
import { fmtAmount, fmtPnl } from '@/utils/format'

const props = defineProps<{
  stocks: Stock[]
}>()

const stockCount = computed(() => props.stocks.length)
const totalPosition = computed(() => props.stocks.reduce((s, st) => s + st.position, 0))
const totalPnl = computed(() => props.stocks.reduce((s, st) => s + st.historical_pnl, 0))
const profitableCount = computed(() => props.stocks.filter(s => s.historical_pnl > 0).length)
</script>
