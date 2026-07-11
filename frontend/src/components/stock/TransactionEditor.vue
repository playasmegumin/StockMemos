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
          :min="0"
          :max="999999999"
          :step="stepUnit"
          style="width: 100%"
        />
      </div>

      <!-- Price -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">价格</label>
        <t-input
          v-model="priceInput"
          type="number"
          :min="0"
          :decimal-places="3"
          placeholder="自动获取中..."
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
import { ref, reactive, computed, onMounted } from 'vue'
import { createTransaction, updateTransaction } from '@/api/transactions'
import { getPrice, getKline } from '@/api/market'
import { getTransactionsByStock } from '@/api/transactions'
import { MessagePlugin } from 'tdesign-vue-next'
import { getDefaultGas } from '@/utils/commission'
import type { Transaction } from '@/types/transaction'
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
dayjs.extend(utc)

const props = defineProps<{
  transaction?: Transaction
  stockId: string
  exchange?: string
  symbol?: string
}>()

const emit = defineEmits<{
  saved: []
  cancel: []
}>()

const isEditing = !!props.transaction
const submitting = ref(false)
const priceInput = ref<string>('')

// 按交易所确定单步增减单位：A股/港股 100 股/手，美股 1 股
const stepUnit = computed(() => {
  if (props.exchange === 'US') return 1
  return 100
})

// 新交易时数量预设为单步步长
const defaultQuantity = computed(() => {
  if (props.transaction) return Math.abs(props.transaction.quantity)
  return stepUnit.value
})

const form = reactive({
  traded_at: props.transaction?.traded_at
    ? dayjs.utc(props.transaction.traded_at).format('YYYY-MM-DD')
    : dayjs().format('YYYY-MM-DD'),
  direction: props.transaction && props.transaction.quantity < 0 ? 'sell' as const : 'buy' as const,
  quantity: defaultQuantity.value,
  price: props.transaction?.price ?? 0,
  gas: props.transaction?.gas ?? getDefaultGas(props.exchange || '', props.symbol || ''),
})

// 编辑已有交易时，把 price 回填到价格输入框
if (props.transaction?.price) {
  priceInput.value = String(props.transaction.price)
}

async function fetchDefaultPrice() {
  if (isEditing && props.transaction?.price) return

  // Tier 1: Current price
  const priceR = await getPrice(props.stockId)
  if (priceR.ok && priceR.data.price > 0) {
    form.price = priceR.data.price
    priceInput.value = String(priceR.data.price)
    return
  }

  // Tier 2: Last kline close
  const klineR = await getKline(props.stockId)
  if (klineR.ok && klineR.data.length > 0) {
    const close = klineR.data[klineR.data.length - 1].close
    form.price = close
    priceInput.value = String(close)
    return
  }

  // Tier 3: Weighted average buy price
  const txnR = await getTransactionsByStock(props.stockId)
  if (txnR.ok && txnR.data.length > 0) {
    const buys = txnR.data.filter(t => t.quantity > 0)
    if (buys.length > 0) {
      const totalQty = buys.reduce((s, t) => s + t.quantity, 0)
      const totalCost = buys.reduce((s, t) => s + t.quantity * t.price, 0)
      form.price = totalCost / totalQty
      priceInput.value = String(form.price)
      return
    }
  }
}

async function handleSubmit() {
  if (form.quantity <= 0) {
    MessagePlugin.warning('请输入有效的数量')
    return
  }

  // 从价格输入框取值
  const parsedPrice = parseFloat(priceInput.value)
  if (isNaN(parsedPrice) || parsedPrice <= 0) {
    MessagePlugin.warning('请输入有效的价格')
    return
  }
  form.price = parsedPrice

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

onMounted(() => {
  if (!isEditing) {
    fetchDefaultPrice()
  }
})
</script>
