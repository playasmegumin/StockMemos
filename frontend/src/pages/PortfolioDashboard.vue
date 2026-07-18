<template>
  <div>
// Header
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">持仓总览</h2>
      <t-button :loading="refreshing" @click="handleRefresh">
        <template #icon><t-icon name="refresh" /></template>
        刷新行情
      </t-button>
    </div>

    <!-- Error alert -->
    <t-alert
      v-if="store.error"
      theme="error"
      :message="store.error"
      class="mb-4"
    >
      <template #operations>
        <t-button size="small" @click="retry">重试</t-button>
      </template>
    </t-alert>

    <!-- Content -->
    <KpiCards
      :total-invested-cny="capitalSummary.total_invested_cny"
      :total-historical-pnl-cny="capitalSummary.total_historical_pnl_cny"
      :total-position-value-cny="capitalSummary.total_position_value_cny"
    />
    <PortfolioTreemap :stocks="store.stocks" />
    <StockTable
      :stocks="store.stocks"
      @delete-stock="openDeleteDialog"
      @add-stock="addDialogVisible = true"
      @refresh-stock="handleRefreshStock"
    />

    <!-- Add Stock Dialog -->
    <t-dialog
      v-model:visible="addDialogVisible"
      header="添加股票"
      :confirm-btn="{ loading: addLoading, content: '确定' }"
      :cancel-btn="{ content: '取消' }"
      @confirm="handleAddStock"
      @close="resetAddForm"
    >
      <t-form :data="addForm" layout="vertical">
        <t-form-item label="代码" name="symbol">
          <t-input v-model="addForm.symbol" placeholder="请输入股票代码（如 518600 / 07709 / DRAM）" />
        </t-form-item>
        <t-form-item label="名称（可选）" name="name">
          <t-input v-model="addForm.name" placeholder="不填则自动查询" />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- Delete Confirmation Dialog -->
    <t-dialog
      v-model:visible="deleteDialogVisible"
      header="确认删除"
      :body="`确定要删除股票「${deleteStockName}」吗？此操作不可恢复。`"
      :confirm-btn="{ loading: deleteLoading, theme: 'danger', content: '删除' }"
      :cancel-btn="{ content: '取消' }"
      @confirm="handleDeleteStock"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue'
import { usePortfolioStore } from '@/stores/portfolio'
import { MessagePlugin } from 'tdesign-vue-next'
import { getCapitalSummary } from '@/api/capital'
import type { CapitalSummary } from '@/api/capital'
import KpiCards from '@/components/dashboard/KpiCards.vue'
import PortfolioTreemap from '@/components/dashboard/PortfolioTreemap.vue'
import StockTable from '@/components/dashboard/StockTable.vue'

const store = usePortfolioStore()
const capitalSummary = reactive<CapitalSummary>({
  total_invested_cny: 0,
  total_historical_pnl_cny: 0,
  total_position_value_cny: 0,
  total_adjustment_cny: 0,
})

// Refresh
const refreshing = ref(false)

async function handleRefresh() {
  refreshing.value = true
  await store.refreshMarket()
  refreshing.value = false
  if (!store.error) {
    MessagePlugin.success('行情刷新完成')
  }
}

function retry() {
  store.fetchAll()
}

// Add Stock Dialog
const addDialogVisible = ref(false)
const addLoading = ref(false)
const addForm = ref({ symbol: '', name: '' })

async function handleAddStock() {
  addLoading.value = true
  const r = await store.addStock(addForm.value)
  addLoading.value = false
  if (r.ok) {
    MessagePlugin.success('添加成功')
    addDialogVisible.value = false
    resetAddForm()
  } else {
    MessagePlugin.warning(r.error || '添加失败')
  }
}

function resetAddForm() {
  addForm.value = { symbol: '', name: '' }
}

// Delete Stock Dialog
const deleteDialogVisible = ref(false)
const deleteStockId = ref('')
const deleteStockName = ref('')
const deleteLoading = ref(false)

function openDeleteDialog(stockId: string) {
  const stock = store.stocks.find(s => s.id === stockId)
  deleteStockId.value = stockId
  deleteStockName.value = stock?.name || ''
  deleteDialogVisible.value = true
}

async function handleDeleteStock() {
  deleteLoading.value = true
  const r = await store.removeStock(deleteStockId.value)
  deleteLoading.value = false
  if (r.ok) {
    deleteDialogVisible.value = false
    MessagePlugin.success('删除成功')
  } else {
    MessagePlugin.warning(r.error || '删除失败')
  }
}

// Refresh Stock — 重新拉取股票基本数据
async function handleRefreshStock(id: string) {
  const r = await store.refreshStock(id)
  if (r.ok) {
    MessagePlugin.success('已刷新')
  } else {
    MessagePlugin.warning(r.error || '刷新失败')
  }
}

// First load — fetch stocks list + capital summary
onMounted(async () => {
  await store.fetchAll()
  const r = await getCapitalSummary()
  if (r.ok && r.data) {
    capitalSummary.total_invested_cny = r.data.total_invested_cny
    capitalSummary.total_historical_pnl_cny = r.data.total_historical_pnl_cny
    capitalSummary.total_position_value_cny = r.data.total_position_value_cny
  }
})
</script>
