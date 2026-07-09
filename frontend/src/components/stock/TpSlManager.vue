<template>
  <div class="tp-sl-manager">
    <!-- Add form -->
    <div v-if="showForm" class="mb-4 border rounded-lg p-4 bg-gray-50 space-y-3">
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="text-xs text-gray-500 block mb-1">类型</label>
          <t-select
            v-model="form.label"
            :options="labelOptions"
            placeholder="选择类型"
            style="width: 100%"
          />
        </div>
        <div>
          <label class="text-xs text-gray-500 block mb-1">价格</label>
          <t-input-number
            v-model="form.price"
            :min="0"
            :decimal-places="3"
            style="width: 100%"
          />
        </div>
        <div>
          <label class="text-xs text-gray-500 block mb-1">备注</label>
          <t-input v-model="form.notes" placeholder="可选备注" style="width: 100%" />
        </div>
      </div>
      <div class="flex gap-2 pt-1">
        <t-button theme="primary" size="small" @click="handleAdd" :loading="submitting">确认</t-button>
        <t-button variant="outline" size="small" @click="closeForm">取消</t-button>
      </div>
    </div>
    <t-button v-else size="small" variant="outline" @click="openForm" class="mb-3">添加止盈止损</t-button>

    <!-- Empty state -->
    <div v-if="stockStore.tpSlPoints.length === 0 && !showForm" class="text-sm text-gray-400 py-4 text-center">
      暂无止盈止损设置
    </div>

    <!-- List -->
    <div v-else class="space-y-2">
      <div
        v-for="point in stockStore.tpSlPoints"
        :key="point.id"
        class="flex items-center justify-between px-4 py-3 border rounded-lg"
      >
        <div class="flex items-center gap-3">
          <t-tag
            :theme="point.label === '止盈' ? 'success' : point.label === '止损' ? 'danger' : 'warning'"
            variant="light"
            size="small"
          >
            {{ point.label }}
          </t-tag>
          <span class="font-mono font-medium">{{ fmtDecimal(point.price) }}</span>
          <span v-if="point.notes" class="text-sm text-gray-400">{{ point.notes }}</span>
        </div>
        <t-link theme="danger" size="small" @click="handleDelete(point)">删除</t-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useStockStore } from '@/stores/stock'
import { fmtDecimal } from '@/utils/format'
import { MessagePlugin, DialogPlugin } from 'tdesign-vue-next'
import type { TpSlPoint } from '@/types/stockAnalyze'

const stockStore = useStockStore()
const showForm = ref(false)
const submitting = ref(false)

const labelOptions = [
  { label: '止盈', value: '止盈' },
  { label: '止损', value: '止损' },
  { label: '目标估值', value: '目标估值' },
]

const form = reactive({
  label: '止盈',
  price: 0,
  notes: '',
})

function openForm() {
  form.label = '止盈'
  form.price = 0
  form.notes = ''
  showForm.value = true
}

function closeForm() {
  showForm.value = false
}

async function handleAdd() {
  if (!form.price || form.price <= 0) {
    MessagePlugin.warning('请输入有效价格')
    return
  }

  submitting.value = true
  const r = await stockStore.addTpSlPoint({
    price: form.price,
    label: form.label,
    notes: form.notes.trim() || undefined,
  })
  if (r.ok) {
    MessagePlugin.success('已添加')
    closeForm()
  } else {
    MessagePlugin.error(r.error || '添加失败')
  }
  submitting.value = false
}

function handleDelete(point: TpSlPoint) {
  const confirmDia = DialogPlugin({
    header: '确认删除',
    body: `确定要删除 "${point.label}" (${fmtDecimal(point.price)}) 吗？`,
    confirmBtn: '删除',
    cancelBtn: '取消',
    theme: 'danger',
    onConfirm: async () => {
      const r = await stockStore.removeTpSlPoint(point.id)
      if (r.ok) {
        MessagePlugin.success('已删除')
        confirmDia.hide()
      } else {
        MessagePlugin.error(r.error || '删除失败')
        confirmDia.hide()
      }
    },
    onClose: () => {
      confirmDia.hide()
    },
  })
}
</script>
