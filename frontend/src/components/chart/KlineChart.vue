<template>
  <div class="kline-chart relative" style="height: 340px">
    <!-- Empty state -->
    <t-empty
      v-if="!klineStore.klineData.length && !klineStore.loading"
      description="暂无日 K 线数据"
    >
      <template #actions>
        <t-button size="small" @click="retry">刷新数据</t-button>
      </template>
    </t-empty>

    <!-- Loading overlay on chart -->
    <div
      v-if="klineStore.loading"
      class="absolute inset-0 z-10 flex items-center justify-center bg-white/60"
    >
      <t-loading />
    </div>

    <!-- Chart -->
    <VChart
      v-if="klineStore.klineData.length > 0"
      ref="chartRef"
      :option="option"
      autoresize
      style="height: 100%; width: 100%"
      @restore="handleRestore"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts'
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DataZoomComponent,
  BrushComponent,
  ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useKlineStore } from '@/stores/kline'
import type { DailyKline } from '@/types/market'

use([
  CandlestickChart,
  BarChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DataZoomComponent,
  BrushComponent,
  ToolboxComponent,
  CanvasRenderer,
])

const klineStore = useKlineStore()
const chartRef = ref<InstanceType<typeof VChart> | null>(null)

// ── Moving average calculator ──
function calcMA(data: DailyKline[], period: number): (number | null)[] {
  return data.map((_, i) => {
    if (i < period - 1) return null
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) {
      sum += data[j].close
    }
    return +(sum / period).toFixed(2)
  })
}

// ── Chart option ──
const option = computed(() => {
  const data = klineStore.klineData
  if (!data.length) return undefined

  const dates = data.map(d => d.date)
  const volumes = data.map(d => d.volume)
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high])
  const ma5 = calcMA(data, 5)
  const ma20 = calcMA(data, 20)
  const ma60 = calcMA(data, 60)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333', fontSize: 12 },
      formatter: function (params: any[]) {
        if (!params || params.length === 0) return ''
        const date = params[0].axisValue
        const candlestick = params.find((p: any) => p.seriesName === 'K线')
        const vol = params.find((p: any) => p.seriesName === '成交量')
        const m5 = params.find((p: any) => p.seriesName === 'MA5')
        const m20 = params.find((p: any) => p.seriesName === 'MA20')
        const m60 = params.find((p: any) => p.seriesName === 'MA60')

        const ohlcData = candlestick?.data ?? []
        let html = `<div style="font-weight:bold;margin-bottom:4px">${date}</div>`
        html += `<div>开盘: ${ohlcData[0]?.toFixed(2) ?? '--'}</div>`
        html += `<div>收盘: ${ohlcData[1]?.toFixed(2) ?? '--'}</div>`
        html += `<div>最低: ${ohlcData[2]?.toFixed(2) ?? '--'}</div>`
        html += `<div>最高: ${ohlcData[3]?.toFixed(2) ?? '--'}</div>`
        if (vol) html += `<div>成交量: ${vol.value}</div>`
        if (m5 && m5.value != null) html += `<div>MA5: ${Number(m5.value).toFixed(2)}</div>`
        if (m20 && m20.value != null) html += `<div>MA20: ${Number(m20.value).toFixed(2)}</div>`
        if (m60 && m60.value != null) html += `<div>MA60: ${Number(m60.value).toFixed(2)}</div>`
        return html
      },
    },

    legend: {
      data: ['K线', 'MA5', 'MA20', 'MA60'],
      top: 0,
      left: 'center',
      textStyle: { fontSize: 11 },
      selected: { K线: true, MA5: true, MA20: true, MA60: true },
    },

    grid: [
      {
        left: '6%',
        right: '6%',
        top: 40,
        height: '60%',
      },
      {
        left: '6%',
        right: '6%',
        top: '78%',
        height: '12%',
      },
    ],

    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#e0e0e0' } },
        axisLabel: { show: false },
        splitLine: { show: true, lineStyle: { color: '#f0f0f0', type: 'dashed' } },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#e0e0e0' } },
        axisLabel: { rotate: 30, fontSize: 10, interval: Math.max(Math.floor(dates.length / 20), 1) },
        splitLine: { show: false },
      },
    ],

    yAxis: [
      {
        type: 'value',
        gridIndex: 0,
        scale: true,
        splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
        axisLine: { show: false },
        axisLabel: { fontSize: 10 },
      },
      {
        type: 'value',
        gridIndex: 1,
        splitLine: { show: false },
        axisLine: { show: false },
        axisLabel: { show: false },
      },
    ],

    series: [
      {
        name: 'K线',
        type: 'candlestick',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ohlc,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a',
        },
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((v, i) => {
          const o = data[i]
          return {
            value: v,
            itemStyle: { color: o.close >= o.open ? '#ef5350' : '#26a69a' },
          }
        }),
      },
      {
        name: 'MA5',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma5,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#ff7043' },
      },
      {
        name: 'MA20',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma20,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#42a5f5' },
      },
      {
        name: 'MA60',
        type: 'line',
        xAxisIndex: 0,
        yAxisIndex: 0,
        data: ma60,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#ab47bc' },
      },
    ],

    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 100,
      },
    ],

    brush: {
      toolbox: ['rect', 'clear'],
      xAxisIndex: 0,
    },
  }
})

function handleRestore() {
  // Brush / toolbox restore — chart resets automatically
}

function retry() {
  if (klineStore.klineData.length === 0) {
    // Re-fetch is handled by the parent; this is a hint for the user
  }
}
</script>
