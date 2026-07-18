<template>
  <div class="h-full">
    <div class="flex justify-between items-center mb-4 flex-shrink-0">
      <h2 class="text-xl font-bold">资金管理</h2>
      <t-button variant="outline" @click="handleRefresh">
        <template #icon><t-icon name="refresh" /></template>
        刷新
      </t-button>
    </div>

    <!-- KPI Cards (2 rows x 4 cols) -->
    <div class="grid grid-cols-4 gap-3 mb-4 flex-shrink-0">
      <div class="kpi-card">
        <div class="kpi-label">总资产</div>
        <div :class="['kpi-value', assetColor]">{{ fmtAmount(totalAsset) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总仓位</div>
        <div :class="['kpi-value', positionColor]">{{ fmtPositionRatio(positionRatio) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总持仓金额</div>
        <div class="kpi-value">{{ fmtAmount(totalPositionValueCny) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">现金</div>
        <div class="kpi-value">{{ fmtAmount(cash) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总投入金额</div>
        <div class="kpi-value">{{ fmtAmount(totalInvestedCny) }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">历史实际总盈亏</div>
        <div :class="['kpi-value', totalHistoricalPnlCny >= 0 ? 'text-red-600' : 'text-green-600']">
          {{ fmtPnl(totalHistoricalPnlCny) }}
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总收益率</div>
        <div :class="['kpi-value', returnRateColor]">
          {{ returnRateDisplay }}
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">总浮盈</div>
        <div :class="['kpi-value', floatPnl >= 0 ? 'text-red-600' : 'text-green-600']">
          {{ fmtPnl(floatPnl) }}
        </div>
      </div>
    </div>

    <!-- Historical Adjustment Section -->
    <section>
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-medium">历史盈亏调整</h3>
        <t-button @click="openAddAdjustment">添加记录</t-button>
      </div>

      <t-table
        :data="pagedAdjustments"
        :columns="adjustmentColumns"
        :loading="adjustmentLoading"
        row-key="id"
        :pagination="adjPagination"
        @page-change="onAdjPageChange"
      >
          <template #adjustmentAmount="{ row }">
            <span :class="row.amount >= 0 ? 'text-red-600' : 'text-green-600'">
              {{ row.amount >= 0 ? '+' : '' }}{{ row.amount }}
            </span>
          </template>
          <template #adjustmentAction="{ row }">
            <t-space size="small">
              <t-link :underline="false" @click="openEditAdjustment(row)">编辑</t-link>
              <t-link theme="danger" :underline="false" @click="handleDeleteAdjustment(row)">删除</t-link>
            </t-space>
          </template>
        </t-table>
    </section>

    <!-- Flow Record Section -->
    <section>
      <div class="flex justify-between items-center mb-3">
        <h3 class="text-lg font-medium">现金流记录</h3>
        <t-button @click="addDialogVisible = true">添加记录</t-button>
      </div>

      <t-table
        :data="pagedFlows"
        :columns="flowColumns"
        :loading="flowLoading"
        row-key="id"
        :pagination="flowPagination"
        @page-change="onFlowPageChange"
      >
          <template #type="{ row }">
            <t-tag v-if="row.type === 'deposit'" theme="success">存入</t-tag>
            <t-tag v-else-if="row.type === 'withdraw'" theme="warning">取出</t-tag>
            <t-tag v-else theme="danger">手续费</t-tag>
          </template>
          <template #amount="{ row }">
            <span :class="row.amount > 0 ? 'text-green-600' : 'text-red-600'">
              {{ row.amount > 0 ? '+' : '' }}{{ row.amount }}
            </span>
          </template>
          <template #action="{ row }">
            <t-link theme="danger" :underline="false" @click="handleDelete(row)">删除</t-link>
          </template>
        </t-table>
    </section>

    <!-- Add Dialog -->
    <t-dialog
      v-model:visible="addDialogVisible"
      header="添加资金记录"
      :confirm-btn="{ loading: addLoading, content: '确定' }"
      :cancel-btn="{ content: '取消' }"
      @confirm="handleAdd"
      @close="resetAddForm"
    >
      <t-form :data="addForm" layout="vertical">
        <t-form-item label="类型" name="type" :rules="[{ required: true }]">
          <t-radio-group v-model="addForm.type">
            <t-radio value="deposit">存入</t-radio>
            <t-radio value="withdraw">取出</t-radio>
            <t-radio value="fee">手续费</t-radio>
          </t-radio-group>
        </t-form-item>
        <t-form-item label="金额" name="amount" :rules="[{ required: true }]">
          <t-input-number
            v-model="addForm.amount"
            :min="0"
            :step="1000"
            placeholder="请输入金额"
            style="width: 100%"
          />
        </t-form-item>
        <t-form-item label="币种" name="currency">
          <t-select v-model="addForm.currency" :options="[
            { label: 'CNY 人民币', value: 'CNY' },
            { label: 'HKD 港币', value: 'HKD' },
            { label: 'USD 美元', value: 'USD' },
          ]" />
        </t-form-item>
        <t-form-item label="备注" name="note">
          <t-textarea v-model="addForm.note" placeholder="可选备注" :rows="2" />
        </t-form-item>
      </t-form>
    </t-dialog>

    <!-- Add/Edit Historical Adjustment Dialog -->
    <t-dialog
      v-model:visible="adjustmentDialogVisible"
      :header="editingAdjustmentId ? '编辑历史盈亏调整' : '添加历史盈亏调整'"
      :confirm-btn="{
        loading: adjustmentSaving,
        content: editingAdjustmentId ? '保存' : '确定',
      }"
      :cancel-btn="{ content: '取消' }"
      @confirm="handleSaveAdjustment"
      @close="resetAdjustmentForm"
    >
      <t-form :data="adjustmentForm" layout="vertical">
        <t-form-item label="金额" name="amount" :rules="[{ required: true }]">
          <t-input-number
            v-model="adjustmentForm.amount"
            :step="100"
            placeholder="请输入调整金额"
            style="width: 100%"
          />
        </t-form-item>
        <t-form-item label="备注" name="note">
          <t-textarea v-model="adjustmentForm.note" placeholder="来源说明" :rows="2" />
        </t-form-item>
      </t-form>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import {
  getCapitalSummary,
  listCapitalFlows,
  createCapitalFlow,
  deleteCapitalFlow,
  listAdjustments,
  createAdjustment,
  updateAdjustment,
  deleteAdjustment,
} from '@/api/capital'
import type { CapitalSummary, CapitalFlow, HistoricalAdjustment } from '@/api/capital'
import { fmtAmount } from '@/utils/format'

const summary = reactive<CapitalSummary>({
  total_invested_cny: 0,
  total_historical_pnl_cny: 0,
  total_position_value_cny: 0,
  total_adjustment_cny: 0,
})

// Computed KPIs
const totalInvestedCny = computed(() => summary.total_invested_cny)
const totalHistoricalPnlCny = computed(
  () => summary.total_historical_pnl_cny + summary.total_adjustment_cny,
)
const totalPositionValueCny = computed(() => summary.total_position_value_cny)
const cash = computed(() => summary.total_invested_cny + summary.total_historical_pnl_cny)
const totalAsset = computed(() => cash.value + summary.total_position_value_cny)
const floatPnl = computed(() => summary.total_position_value_cny + summary.total_historical_pnl_cny)
const adjustedTotalAsset = computed(() => totalAsset.value + summary.total_adjustment_cny)
const isPaidBack = computed(() => summary.total_invested_cny <= 0)
const returnRate = computed(() => {
  if (isPaidBack.value) return 1
  return adjustedTotalAsset.value / summary.total_invested_cny
})
const returnRateDisplay = computed(() =>
  isPaidBack.value ? '已回本' : fmtReturnRate(returnRate.value),
)
const returnRateColor = computed(() => {
  if (isPaidBack.value) return ''
  return returnRate.value >= 1 ? 'text-red-600' : 'text-green-600'
})
const positionRatio = computed(() => {
  if (totalAsset.value === 0) return 0
  return summary.total_position_value_cny / totalAsset.value
})

function fmtPnl(val: number): string {
  if (val === 0) return '0.00'
  const sign = val > 0 ? '+' : '-'
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

// 总资产颜色: >总投入=红(涨), <总投入=绿(跌)
const assetColor = computed(() => {
  if (totalAsset.value > summary.total_invested_cny) return 'text-red-600'
  if (totalAsset.value < summary.total_invested_cny) return 'text-green-600'
  return ''
})

// 总仓位颜色: >80%=绿(重仓), <50%=红(轻仓), 中间=黑
const positionColor = computed(() => {
  if (positionRatio.value > 0.8) return 'text-green-600'
  if (positionRatio.value < 0.5) return 'text-red-600'
  return ''
})

const flows = ref<CapitalFlow[]>([])
const flowLoading = ref(false)
const flowPagination = reactive({ defaultPageSize: 5, total: 0, current: 1, pageSizeOptions: [5, 10, 20] })
const adjPagination = reactive({ defaultPageSize: 5, total: 0, current: 1, pageSizeOptions: [5, 10, 20] })

const pagedFlows = computed(() => {
  const start = (flowPagination.current - 1) * flowPagination.defaultPageSize
  return flows.value.slice(start, start + flowPagination.defaultPageSize)
})
const pagedAdjustments = computed(() => {
  const start = (adjPagination.current - 1) * adjPagination.defaultPageSize
  return adjustments.value.slice(start, start + adjPagination.defaultPageSize)
})

const flowColumns = [
  { colKey: 'created_at', title: '时间', width: 180 },
  { colKey: 'type', title: '类型', width: 100, cell: 'type' },
  { colKey: 'amount', title: '金额', width: 150, cell: 'amount' },
  { colKey: 'currency', title: '币种', width: 80 },
  { colKey: 'note', title: '备注', ellipsis: true },
  { colKey: 'action', title: '操作', width: 80, cell: 'action' },
]

const adjustments = ref<HistoricalAdjustment[]>([])
const adjustmentLoading = ref(false)
const adjustmentColumns = [
  { colKey: 'created_at', title: '创建时间', width: 180 },
  { colKey: 'amount', title: '金额', width: 150, cell: 'adjustmentAmount' },
  { colKey: 'note', title: '备注', ellipsis: true },
  { colKey: 'action', title: '操作', width: 120, cell: 'adjustmentAction' },
]

async function loadData() {
  flowLoading.value = true
  adjustmentLoading.value = true
  const [sr, fr, ar] = await Promise.all([
    getCapitalSummary(),
    listCapitalFlows(1000, 0),
    listAdjustments(),
  ])
  flowLoading.value = false
  adjustmentLoading.value = false

  if (sr.ok && sr.data) {
    summary.total_invested_cny = sr.data.total_invested_cny
    summary.total_historical_pnl_cny = sr.data.total_historical_pnl_cny
    summary.total_position_value_cny = sr.data.total_position_value_cny
    summary.total_adjustment_cny = sr.data.total_adjustment_cny
  }
  if (fr.ok && fr.data) {
    flows.value = fr.data
    flowPagination.total = fr.data.length
  }
  if (ar.ok && ar.data) {
    adjustments.value = ar.data
    adjPagination.total = ar.data.length
  }
  // Clamp current page to a valid range after data reload
  const flowMaxPage = Math.max(1, Math.ceil(flows.value.length / flowPagination.defaultPageSize))
  if (flowPagination.current > flowMaxPage) flowPagination.current = flowMaxPage
  const adjMaxPage = Math.max(1, Math.ceil(adjustments.value.length / adjPagination.defaultPageSize))
  if (adjPagination.current > adjMaxPage) adjPagination.current = adjMaxPage
}

function handleRefresh() {
  loadData()
}

function onFlowPageChange({ current, pageSize }: { current: number; pageSize: number }) {
  flowPagination.current = current
  flowPagination.defaultPageSize = pageSize
}
function onAdjPageChange({ current, pageSize }: { current: number; pageSize: number }) {
  adjPagination.current = current
  adjPagination.defaultPageSize = pageSize
}

// Add Dialog
const addDialogVisible = ref(false)
const addLoading = ref(false)
const addForm = reactive({
  type: 'deposit' as 'deposit' | 'withdraw' | 'fee',
  amount: 0,
  currency: 'CNY',
  note: '',
})

async function handleAdd() {
  if (addForm.amount <= 0) {
    MessagePlugin.warning('请输入有效的正数金额')
    return
  }
  addLoading.value = true
  const r = await createCapitalFlow({
    type: addForm.type,
    amount: addForm.amount,
    currency: addForm.currency,
    note: addForm.note || undefined,
  })
  addLoading.value = false
  if (r.ok) {
    MessagePlugin.success('添加成功')
    addDialogVisible.value = false
    resetAddForm()
    flowPagination.current = 1
    loadData()
  } else {
    MessagePlugin.warning(r.error || '添加失败')
  }
}

function resetAddForm() {
  addForm.type = 'deposit'
  addForm.amount = 0
  addForm.currency = 'CNY'
  addForm.note = ''
}

async function handleDelete(row: CapitalFlow) {
  const r = await deleteCapitalFlow(row.id)
  if (r.ok) {
    MessagePlugin.success('已删除')
    loadData()
  } else {
    MessagePlugin.warning(r.error || '删除失败')
  }
}

// Historical Adjustment Dialog
const adjustmentDialogVisible = ref(false)
const adjustmentSaving = ref(false)
const editingAdjustmentId = ref<string | null>(null)
const adjustmentForm = reactive({
  amount: 0,
  note: '',
})

function openAddAdjustment() {
  resetAdjustmentForm()
  adjustmentDialogVisible.value = true
}

function openEditAdjustment(row: HistoricalAdjustment) {
  editingAdjustmentId.value = row.id
  adjustmentForm.amount = row.amount
  adjustmentForm.note = row.note || ''
  adjustmentDialogVisible.value = true
}

async function handleSaveAdjustment() {
  if (adjustmentForm.amount === 0) {
    MessagePlugin.warning('调整金额不能为 0')
    return
  }
  adjustmentSaving.value = true
  const payload = {
    amount: adjustmentForm.amount,
    note: adjustmentForm.note || undefined,
  }
  const editingId = editingAdjustmentId.value
  const r = editingId
    ? await updateAdjustment(editingId, payload)
    : await createAdjustment(payload)
  adjustmentSaving.value = false
  if (r.ok) {
    MessagePlugin.success(editingId ? '更新成功' : '添加成功')
    adjustmentDialogVisible.value = false
    resetAdjustmentForm()
    adjPagination.current = 1
    await loadData()
  } else {
    MessagePlugin.warning(r.error || (editingId ? '更新失败' : '添加失败'))
  }
}

function resetAdjustmentForm() {
  editingAdjustmentId.value = null
  adjustmentForm.amount = 0
  adjustmentForm.note = ''
}

function handleDeleteAdjustment(row: HistoricalAdjustment) {
  const confirmDia = DialogPlugin({
    header: '确认删除',
    body: '确定要删除这条历史盈亏调整记录吗？此操作不可恢复。',
    confirmBtn: '删除',
    cancelBtn: '取消',
    theme: 'danger',
    onConfirm: async () => {
      const r = await deleteAdjustment(row.id)
      confirmDia.hide()
      if (r.ok) {
        MessagePlugin.success('已删除')
        await loadData()
      } else {
        MessagePlugin.warning(r.error || '删除失败')
      }
    },
    onClose: () => {
      confirmDia.hide()
    },
  })
}

onMounted(() => {
  loadData()
})
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
