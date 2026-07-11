<template>
  <div class="grid grid-cols-4 gap-3 mb-4">
    <!-- 总资产 -->
    <div class="kpi-card" style="border-left: 3px solid #1677ff">
      <div class="kpi-label">总资产</div>
      <div :class="['kpi-value', assetColor]">{{ fmtAmount(totalAsset) }}</div>
    </div>

    <!-- 总收益率 -->
    <div class="kpi-card" style="border-left: 3px solid #52c41a">
      <div class="kpi-label">总收益率</div>
      <div :class="['kpi-value', returnColor]">
        {{ fmtReturnRate(returnRate) }}
      </div>
    </div>

    <!-- 总仓位 -->
    <div class="kpi-card" style="border-left: 3px solid #faad14">
      <div class="kpi-label">总仓位</div>
      <div :class="['kpi-value', positionColor]">{{ fmtPositionRatio(positionRatio) }}</div>
    </div>

    <!-- 总浮盈 -->
    <div class="kpi-card" style="border-left: 3px solid #722ed1">
      <div class="kpi-label">总浮盈</div>
      <div :class="['kpi-value', floatPnlColor]">{{ fmtPnl(floatPnl) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { fmtAmount } from '@/utils/format'

const props = defineProps<{
  totalInvestedCny: number
  totalHistoricalPnlCny: number
  totalPositionValueCny: number
}>()

const cash = computed(() => props.totalInvestedCny + props.totalHistoricalPnlCny)
const totalAsset = computed(() => cash.value + props.totalPositionValueCny)
const floatPnl = computed(() => props.totalPositionValueCny + props.totalHistoricalPnlCny)
const returnRate = computed(() => {
  if (props.totalInvestedCny === 0) return 1
  return totalAsset.value / props.totalInvestedCny
})
const positionRatio = computed(() => {
  if (totalAsset.value === 0) return 0
  return props.totalPositionValueCny / totalAsset.value
})

// 总资产颜色: >总投入=红(涨), <总投入=绿(跌)
const assetColor = computed(() => {
  if (totalAsset.value > props.totalInvestedCny) return 'text-red-600'
  if (totalAsset.value < props.totalInvestedCny) return 'text-green-600'
  return ''
})

// 总收益率颜色: 正=红, 负=绿
const returnColor = computed(() => {
  if (returnRate.value > 1) return 'text-red-600'
  if (returnRate.value < 1) return 'text-green-600'
  return ''
})

// 总仓位颜色: >80%=绿(重仓), <50%=红(轻仓), 中间=黑
const positionColor = computed(() => {
  if (positionRatio.value > 0.8) return 'text-green-600'
  if (positionRatio.value < 0.5) return 'text-red-600'
  return ''
})

// 总浮盈颜色: >=0=红(浮盈), <0=绿(浮亏)
const floatPnlColor = computed(() => {
  if (floatPnl.value >= 0) return 'text-red-600'
  return 'text-green-600'
})

function fmtPnl(val: number): string {
  if (val === 0) return '0.00'
  const sign = val > 0 ? '+' : ''
  return `${sign}${fmtAmount(Math.abs(val))}`
}

function fmtReturnRate(rate: number): string {
  const pct = (rate - 1) * 100
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

function fmtPositionRatio(ratio: number): string {
  return `${(ratio * 100).toFixed(1)}%`
}
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
.text-red-600 { color: #e53e3e; }
.text-green-600 { color: #38a169; }
</style>
