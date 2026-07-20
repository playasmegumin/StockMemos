<template>
  <div class="transaction-list">
    <!-- Add button / Editor -->
    <div v-if="showEditor" class="mb-4">
      <TransactionEditor
        :stock-id="stockStore.stock!.id"
        :exchange="stockStore.stock!.exchange"
        :symbol="stockStore.stock!.symbol"
        :transaction="editingTransaction ?? undefined"
        @saved="handleSaved"
        @cancel="closeEditor"
      />
    </div>
    <t-button v-else size="small" variant="outline" @click="openAddEditor" class="mb-3">
      添加交易
    </t-button>

    <!-- Table -->
    <t-table
      :data="transactions"
      :columns="columns"
      row-key="id"
      :pagination="pagination"
      :loading="loading"
      @page-change="handlePageChange"
      size="small"
      bordered
      hover
    >
      <!-- traded_at -->
      <template #traded_at="{ row }">
        <span>{{ fmtDate(row.traded_at) }}</span>
      </template>

      <!-- quantity -->
      <template #quantity="{ row }">
        <span :class="row.quantity >= 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'">
          {{ row.quantity >= 0 ? '+' : '' }}{{ row.quantity }}
        </span>
      </template>

      <!-- price -->
      <template #price="{ row }">
        <span class="font-mono">{{ fmtDecimal(row.price) }}</span>
      </template>

      <!-- gas -->
      <template #gas="{ row }">
        <span class="font-mono">{{ fmtDecimal(row.gas) }}</span>
      </template>

      <!-- total -->
      <template #total="{ row }">
        <span
          class="font-mono"
          :class="row.quantity >= 0 ? 'text-red-600' : 'text-green-600'"
        >
          {{ fmtDecimal(row.quantity * row.price + row.gas) }}
        </span>
      </template>

      <!-- actions -->
      <template #actions="{ row }">
        <t-space>
          <t-link theme="primary" size="small" @click="openEditEditor(row)">编辑</t-link>
          <t-link theme="danger" size="small" @click="handleDelete(row)">删除</t-link>
        </t-space>
      </template>
    </t-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, h } from 'vue'
import { useStockStore } from '@/stores/stock'
import { getTransactionsByStock, deleteTransaction } from '@/api/transactions'
import { fmtDate, fmtDecimal } from '@/utils/format'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import type { Transaction } from '@/types/transaction'
import TransactionEditor from './TransactionEditor.vue'

const stockStore = useStockStore()

const emit = defineEmits<{
  changed: []
}>()

const transactions = ref<Transaction[]>([])
const loading = ref(false)
const showEditor = ref(false)
const editingTransaction = ref<Transaction | null>(null)

const pagination = reactive({
  defaultPageSize: 20,
  total: 0,
  current: 1,
  showPageSize: false,
})

const columns = [
  { colKey: 'traded_at', title: '日期', sorter: true, sortType: 'all', width: 120 },
  { colKey: 'quantity', title: '股数', sorter: true, sortType: 'all', width: 100 },
  { colKey: 'price', title: '价格', width: 100 },
  { colKey: 'gas', title: '佣金', width: 90 },
  { colKey: 'total', title: '总金额', width: 120 },
  { colKey: 'actions', title: '操作', width: 120, align: 'center' as const },
]

async function fetchTransactions() {
  if (!stockStore.stock) return
  loading.value = true
  try {
    const r = await getTransactionsByStock(stockStore.stock.id)
    if (r.ok) {
      transactions.value = r.data
      pagination.total = r.data.length
    } else {
      MessagePlugin.error(r.error || '加载交易记录失败')
    }
  } finally {
    loading.value = false
  }
}

function openAddEditor() {
  editingTransaction.value = null
  showEditor.value = true
}

function openEditEditor(tx: Transaction) {
  editingTransaction.value = tx
  showEditor.value = true
}

function closeEditor() {
  showEditor.value = false
  editingTransaction.value = null
}

async function handleSaved() {
  closeEditor()
  await fetchTransactions()
  emit('changed')
}

function handlePageChange(pageInfo: any) {
  pagination.current = pageInfo.current
}

function handleDelete(row: Transaction) {
  const confirmDia = DialogPlugin({
    header: '确认删除',
    body: `确定要删除 ${fmtDate(row.traded_at)} 的交易记录吗？此操作不可恢复。`,
    confirmBtn: '删除',
    cancelBtn: '取消',
    theme: 'danger',
    onConfirm: async () => {
      try {
        const r = await deleteTransaction(row.id)
        if (r.ok) {
          MessagePlugin.success('交易已删除')
          await fetchTransactions()
          emit('changed')
        } else {
          MessagePlugin.error(r.error || '删除失败')
        }
      } catch {
        MessagePlugin.error('删除失败')
      } finally {
        confirmDia.hide()
      }
    },
    onClose: () => {
      confirmDia.hide()
    },
  })
}

defineExpose({ handleSaved, handleDelete })

onMounted(() => {
  if (stockStore.stock) {
    fetchTransactions()
  }
})
</script>
