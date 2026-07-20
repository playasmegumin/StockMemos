<template>
  <!-- 标题行：与持仓列表标题样式一致，无多余内边距 -->
  <div class="flex justify-between items-center mb-3">
    <span class="text-lg font-medium">持仓地图</span>
    <span class="text-xs text-gray-400">方块面积 = 仓位占比</span>
  </div>

  <!-- 白色卡片：仅包裹 Treemap 图表 -->
  <div class="bg-white rounded-2xl shadow-sm mb-4 w-full">
    <div class="p-6">
      <t-empty v-if="!hasHoldings && !loading" description="暂无持仓数据" />

      <div v-else-if="loading" class="flex items-center justify-center" style="height: 360px">
        <t-loading />
      </div>

      <!-- Treemap — 居中，不超过版面 60%，16:9 -->
      <div v-else class="flex justify-center" style="width:100%">
        <VChart
          ref="chartRef"
          :option="chartOption"
          autoresize
          style="width: 100%; max-width: 60%; aspect-ratio: 16/9; min-height: 250px"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { TreemapChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { Stock } from '@/types/stock'
import { getAnalyze, getTags } from '@/api/stockAnalyze'
import { computeAllPositionValues } from '@/utils/positionValue'
import { fmtAmount, fmtPnl } from '@/utils/format'

use([TreemapChart, TooltipComponent, CanvasRenderer])

const props = defineProps<{
  stocks: Stock[]
  refreshTrigger?: number
}>()

const loading = ref(true)
const chartRef = ref<InstanceType<typeof VChart> | null>(null)
const positionValues = ref(new Map<string, { value: number; price: number; source: string }>())
const stockTags = ref(new Map<string, string[]>()
)

const TAG_COLORS = ['#FF6B35', '#4ECDC4', '#FFD93D', '#6C5CE7', '#FF2D7F', '#00BCD4', '#00C853', '#FF9800']

function hashTag(tag: string): number {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = ((hash << 5) - hash) + tag.charCodeAt(i); hash |= 0
  }
  return Math.abs(hash)
}

function getColor(tags: string[]): string {
  if (!tags || tags.length === 0) return TAG_COLORS[0]  // first palette color for untagged
  return TAG_COLORS[hashTag(tags[0]) % TAG_COLORS.length]
}

const hasHoldings = computed(() => props.stocks.some(s => s.position > 0))

// ── Build hierarchical treemap data ──
const treemapData = computed(() => {
  const pv = positionValues.value
  const tagMap = stockTags.value
  const totalValue = Array.from(pv.values()).reduce((s, v) => s + v.value, 0)
  if (totalValue <= 0) return []
  const MIN_PCT = 5  // minimum tile display size (%)

  // Build enriched stock entries
  const stockEntries = props.stocks
    .filter(s => s.position > 0 && pv.has(s.id) && pv.get(s.id)!.value > 0)
    .map(s => {
      const v = pv.get(s.id)!
      const tags = tagMap.get(s.id) || []
      const pct = (v.value / totalValue) * 100
      const primaryTag = tags.length > 0 ? tags[0] : '__untagged__'
      return { stock: s, pv: v, primaryTag, pct }
    })
    .sort((a, b) => b.pv.value - a.pv.value)

  // Step 1: any stock < 3% → "其他", removed from original tag group
  const OTHER_THRESHOLD = 2
  const normalEntries = stockEntries.filter(e => e.pct >= OTHER_THRESHOLD)
  const smallEntries = stockEntries.filter(e => e.pct < OTHER_THRESHOLD)

  // Step 2: group normal entries by primary tag
  const tagGroups = new Map<string, typeof normalEntries>()
  for (const e of normalEntries) {
    const group = tagGroups.get(e.primaryTag) || []
    group.push(e)
    tagGroups.set(e.primaryTag, group)
  }

  // Build level-1 children: one group per tag
  const MIN_VALUE = totalValue * MIN_PCT / 100
  const children: any[] = []
  for (const [tagName, entries] of tagGroups) {
    const tagDisplayName = tagName === '__untagged__' ? '未分类' : tagName
    const tagColor = getColor(tagName === '__untagged__' ? [] : [tagName])
    const subChildren = entries.map(e => {
      const realPct = e.pct.toFixed(1) + '%'
      const pnlInfo = fmtPnl(e.stock.historical_pnl)
      return {
        name: e.stock.name,
        value: Math.max(e.pv.value, MIN_VALUE), // at least MIN_PCT% display size
        pct: realPct,
        symbol: e.stock.symbol,
        stockName: e.stock.name,
        tagName: tagDisplayName,
        marketValue: fmtAmount(e.pv.value),
        pnl: pnlInfo.text,
        pnlCls: pnlInfo.cls,
        itemStyle: { color: getColor(tagMap.get(e.stock.id) || []) },
      }
    })

    children.push({
      name: tagDisplayName,
      itemStyle: { color: tagColor },
      children: subChildren,
    })
  }

  // Step 3: add "其他" group for <2% stocks
  if (smallEntries.length > 0) {
    const otherValue = smallEntries.reduce((s, e) => s + e.pv.value, 0)
    const otherPct = ((otherValue / totalValue) * 100).toFixed(1)

    // Build multi-line label: first line "其他 X.X%", then one stock per line
    const otherLines = smallEntries.map(e =>
      `${e.stock.name} ${e.pct.toFixed(1)}%`
    ).join('\n')

    children.push({
      name: '其他',
      itemStyle: { color: '#D0D0D0' },
      children: [{
        name: `其他 ${otherPct}%\n` + otherLines,
        isOther: true,
        value: Math.max(otherValue, MIN_VALUE),
        itemStyle: { color: '#D0D0D0' },
      }]
    })
  }

  return children
})

const chartOption = computed(() => {
  const children = treemapData.value
  if (children.length === 0) return {}

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.96)',
      borderColor: '#e0e0e0',
      borderWidth: 1,
      padding: [10, 14],
      formatter: (params: any) => {
          const d = params.data
          if (!d) return ''
          // Skip non-leaf nodes (tag groups, root) — only show tooltip on stock tiles
          if (!d.isOther && !d.stockName) return ''
          // "其他" group child
          if (d.isOther) {
            const lines = (d.name || '').split('\n')
            const title = lines[0]  // "其他 X.X%"
            const items = lines.slice(1)  // stock list
            return `<div style="font-weight:600;font-size:14px;margin-bottom:4px">${title}</div><div style="font-size:12px;color:#666">${items.join('<br>') || '(空)'}</div>`
          }
          return `
            <div style="font-weight:600;font-size:14px;margin-bottom:4px">${d.stockName || ''}</div>
            <div style="font-size:12px;color:#888">${d.symbol || ''} · ${d.tagName || ''}</div>
            <div style="margin-top:6px">
              <div>持仓市值: <b>${d.marketValue || ''}</b></div>
              <div>盈亏: <b style="color:${d.pnlCls?.includes('red') ? '#e74c3c' : '#27ae60'}">${d.pnl || ''}</b></div>
              <div>占比: <b>${d.pct || ''}</b></div>
            </div>
          `
        },
    },
    series: [{
      type: 'treemap',
      data: children,
      roam: false,
      nodeClick: false,
      breadcrumb: { show: false },
      visibleMin: 5,
      width: '100%',
      height: '100%',

      // Level 1 (tag groups): label centered, tag name
      // Level 2 (stock tiles): label centered, name + pct
      levels: [
        { // Level 0: root — no label
          colorMappingBy: 'data',
        },
        { // Level 1: tag groups
          colorMappingBy: 'data',
          label: {
            show: true,
            position: 'inside',
            color: '#fff',
            fontSize: 16,
            fontWeight: 'bold',
          },
          itemStyle: {
            borderRadius: 12,
            borderColor: '#fff',
            borderWidth: 8,
          },
        },
        { // Level 2: stock tiles
          colorMappingBy: 'data',
          label: {
            show: true,
            position: 'inside',
            fontSize: 27,
            fontWeight: 'bold',
            lineHeight: 33,
            color: '#fff',
            overflow: 'truncate',
            formatter: (params: any) => {
              const d = params.data
              if (!d) return ''
              if (d.isOther) {
                // name = "其他 X.X%\nstock1 Y.Y%\n..."
                const lines = (d.name || '').split('\n')
                return lines[0]  // only show "其他 X.X%" in the tile
              }
              return (d.stockName || '') + '\n' + (d.pct || '')
            },
          },
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 3,
          },
        },
      ],
    }],
  }
})

async function loadData() {
  loading.value = true
  try {
    const pv = await computeAllPositionValues(props.stocks)
    positionValues.value = pv

    const tagMap = new Map<string, string[]>()
    const activeStocks = props.stocks.filter(s => s.position > 0)
    const analyzeResults = await Promise.all(activeStocks.map(s => getAnalyze(s.id)))
    await Promise.all(analyzeResults.map(async (r, i) => {
      if (!r.ok) return
      const tagsR = await getTags(r.data.id)
      if (tagsR.ok) tagMap.set(activeStocks[i].id, tagsR.data.map(t => t.tag))
    }))
    stockTags.value = tagMap
  } catch {
    // Data loading failed — keep existing positionValues and stockTags intact
  } finally {
    loading.value = false
    // Force chart resize after data loads to ensure correct layout
    nextTick(() => { chartRef.value?.resize() })
  }
}

onMounted(loadData)
// Refresh trigger prop — parent bumps this counter to force a reload
watch(() => props.refreshTrigger, () => { if (props.stocks.length > 0) loadData() })

defineExpose({ loadData, loading, positionValues })
</script>
