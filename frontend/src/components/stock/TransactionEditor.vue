<template>
  <div class="transaction-editor border rounded-lg p-4 bg-gray-50 space-y-3">
    <div class="text-sm font-semibold text-gray-700 mb-2">
      {{ isEditing ? '编辑交易' : '添加交易' }}
    </div>

    <div class="grid grid-cols-2 gap-3">
      <!-- Date -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">日期</label>
        <t-date-picker
          v-model="form.traded_at"
          mode="date"
          format="YYYY-MM-DD"
          style="width: 100%"
        />
      </div>

      <!-- Direction -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">方向</label>
        <t-radio-group v-model="form.direction">
          <t-radio-button value="buy">买入</t-radio-button>
          <t-radio-button value="sell">卖出</t-radio-button>
        </t-radio-group>
      </div>

      <!-- Quantity -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">数量</label>
        <t-input-number
          v-model="form.quantity"
          :min="1"
          :max="999999999"
          :step="100"
          style="width: 100%"
        />
      </div>

      <!-- Price -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">价格</label>
        <t-input-number
          v-model="form.price"
          :min="0.001"
          :decimal-places="3"
          style="width: 100%"
        />
      </div>

      <!-- Gas -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">佣金 (Gas)</label>
        <t-input-number
          v-model="form.gas"
          :min="0"
          :decimal-places="2"
          style="width: 100%"
        />
      </div>
    </div>

    <div class="flex gap-2 pt-2">
      <t-button theme="primary" size="small" @click="handleSubmit" :loading="submitting">
        {{ isEditing ? '保存修改' : '确认添加' }}
      </t-button>
      <t-button variant="outline" size="small" @click="$emit('cancel')">取消</t-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { createTransaction, updateTransaction } from '@/api/transactions'
import { MessagePlugin } from 'tdesign-vue-next'
import type { Transaction } from '@/types/transaction'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

const props = defineProps<{
  transaction?: Transaction
  stockId: string
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const isEditing = !!props.transaction
const submitting = ref(false)

const form = reactive({
  traded_at: props.transaction?.traded_at
    ? dayjs.utc(props.transaction.traded_at).format('YYYY-MM-DD')
    : dayjs().format('YYYY-MM-DD'),
  direction: props.transaction && props.transaction.quantity < 0 ? 'sell' as const : 'buy' as const,
  quantity: props.transaction ? Math.abs(props.transaction.quantity) : 100,
  price: props.transaction?.price ?? 0,
  gas: props.transaction?.gas ?? 0,
})

async function handleSubmit() {
  if (!form.quantity || form.quantity <= 0) {
    MessagePlugin.warning('请输入有效的数量')
    return
  }
  if (!form.price || form.price <= 0) {
    MessagePlugin.warning('请输入有效的价格')
    return
  }

  submitting.value = true

  const signedQuantity = form.direction === 'sell' ? -form.quantity : form.quantity

  if (isEditing && props.transaction) {
    const r = await updateTransaction(props.transaction.id, {
      quantity: signedQuantity,
      price: form.price,
      gas: form.gas,
      traded_at: form.traded_at,
    })
    if (r.ok) {
      MessagePlugin.success('交易已更新')
      emit('saved')
    } else {
      MessagePlugin.error(r.error || '更新失败')
    }
  } else {
    const r = await createTransaction({
      stock_id: props.stockId,
      quantity: signedQuantity,
      price: form.price,
      gas: form.gas,
      traded_at: form.traded_at,
    })
    if (r.ok) {
      MessagePlugin.success('交易已添加')
      emit('saved')
    } else {
      MessagePlugin.error(r.error || '添加失败')
    }
  }

  submitting.value = false
}
</script>
