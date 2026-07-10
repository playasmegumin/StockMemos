<template>
  <div class="grid grid-cols-4 gap-3 mb-4">
    <!-- 收益 -->
    <div class="kpi-card" style="border-left: 3px solid #FF6B35">
      <div class="kpi-label">收益</div>
      <div :class="['kpi-value', totalPnl >= 0 ? 'text-red-600' : 'text-green-600']">
        {{ fmtPnl(totalPnl).text }}
      </div>
    </div>

    <!-- 股票 -->
    <div class="kpi-card" style="border-left: 3px solid #4ECDC4">
      <div class="kpi-label">股票</div>
      <div class="kpi-value">{{ stockCount }}</div>
    </div>

    <!-- 总持仓金额 -->
    <div class="kpi-card" style="border-left: 3px solid #FFD93D">
      <div class="kpi-label">总持仓金额</div>
      <div class="kpi-value">{{ fmtAmount(totalPositionValue) }}</div>
    </div>

    <!-- 现金 -->
    <div class="kpi-card" style="border-left: 3px solid #6C5CE7">
      <div class="kpi-label">现金</div>
      <div class="kpi-value">{{ fmtAmount(0) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Stock } from '@/types/stock'
import { fmtAmount, fmtPnl } from '@/utils/format'

const props = defineProps<{
  stocks: Stock[]
  totalPositionCny?: number
}>()

const stockCount = computed(() => props.stocks.length)
const totalPnl = computed(() => props.stocks.reduce((s, st) => s + st.historical_pnl, 0))
const totalPositionValue = computed(() => props.totalPositionCny ?? 0)
</script>

<style scoped>
.kpi-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-label {
  font-size: 12px;
  color: #8B8B9A;
  margin-bottom: 4px;
}
.kpi-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
}
</style>
