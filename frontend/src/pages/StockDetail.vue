<template>
  <div v-if="stockStore.stock" class="stock-detail grid grid-cols-[300px_1fr] grid-rows-[auto_1fr] gap-4 h-full">
    <div class="col-span-2 row-span-1 flex items-center gap-4 p-4 bg-white rounded-lg shadow-sm">
      <t-link theme="primary" @click="router.push('/')">← 返回列表</t-link>
      <div class="text-xl font-bold">
        {{ stockStore.stock.name }}
        <span class="text-gray-400 font-normal text-base ml-1">
          ({{ stockStore.stock.exchange }}.{{ stockStore.stock.symbol }})
        </span>
      </div>
      <t-button
        variant="outline"
        size="small"
        :loading="klineStore.loading"
        @click="handleRefresh"
      >
        刷新行情
      </t-button>
    </div>

    <!-- Left panel -->
    <div class="col-span-1 row-span-1 overflow-auto">
      <InfoPanel />
    </div>

    <!-- Right side -->
    <div class="stock-detail-right grid grid-rows-[auto_1fr] gap-4 overflow-hidden min-h-0">
      <div class="bg-white rounded-lg shadow-sm p-4">
        <KlineChart />
      </div>
      <div class="bg-white rounded-lg shadow-sm p-4 overflow-y-auto min-h-0">
        <t-tabs default-value="transactions" size="medium">
          <t-tab-panel value="transactions" label="交易记录">
            <TransactionList />
          </t-tab-panel>
          <t-tab-panel value="reports" label="分析报告">
            <ReportList />
          </t-tab-panel>
          <t-tab-panel value="tpsl" label="止盈止损">
            <TpSlManager />
          </t-tab-panel>
          <t-tab-panel value="memos" label="投资备忘">
            <StockMemosTab :stock-id="stockStore.stock.id" />
          </t-tab-panel>
        </t-tabs>
      </div>
    </div>
  </div>

  <!-- Loading overlay -->
  <div v-else-if="stockStore.loading || klineStore.loading" class="flex items-center justify-center h-64">
    <t-loading />
  </div>

  <!-- Error state -->
  <t-alert
    v-else-if="stockStore.error"
    theme="error"
    :message="stockStore.error"
    class="my-4"
  >
    <template #operation>
      <t-button size="small" @click="loadData">重试</t-button>
    </template>
  </t-alert>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStockStore } from '@/stores/stock'
import { useKlineStore } from '@/stores/kline'
import { MessagePlugin } from 'tdesign-vue-next'
import InfoPanel from '@/components/stock/InfoPanel.vue'
import KlineChart from '@/components/chart/KlineChart.vue'
import TransactionList from '@/components/stock/TransactionList.vue'
import ReportList from '@/components/stock/ReportList.vue'
import TpSlManager from '@/components/stock/TpSlManager.vue'
import StockMemosTab from '@/components/detail/StockMemosTab.vue'

const route = useRoute()
const router = useRouter()
const stockStore = useStockStore()
const klineStore = useKlineStore()

const stockId = route.params.id as string

async function loadData() {
  await Promise.all([
    stockStore.fetchAll(stockId),
    klineStore.fetchKline(stockId),
  ])
}

async function handleRefresh() {
  await stockStore.refreshMarket()
  await klineStore.fetchKline(stockId)
  MessagePlugin.success('行情已刷新')
}

onMounted(loadData)

onUnmounted(() => {
  stockStore.$reset()
  // intentionally keep klineStore data
})
</script>

<style scoped>
/* Inline critical grid layout to avoid UnoCSS injection timing issues */
.stock-detail {
  display: grid;
  grid-template-columns: 300px 1fr;
  grid-template-rows: auto 1fr;
  gap: 1rem;
  height: 100%;
}
.stock-detail > :nth-child(1) {
  grid-column: span 2;
  grid-row: span 1;
}
.stock-detail > :nth-child(2) {
  grid-column: span 1;
  grid-row: span 1;
}
.stock-detail > :nth-child(3) {
  grid-column: span 1;
  grid-row: span 1;
}
/* Right side inner grid */
.stock-detail-right {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 1rem;
  overflow: hidden;
  min-height: 0;
}
</style>
