<template>
  <div>
    <h2 class="text-xl font-bold mb-4">设置</h2>

    <!-- 配置信息 -->
    <t-card title="配置信息" class="mb-4">
      <!-- 汇率配置 -->
      <h3 class="text-lg font-medium mb-3">汇率配置</h3>
      <t-table :data="rates" :columns="rateColumns" row-key="currency" :loading="loading">
        <template #rate_to_cny="{ row }">
          <t-input-number
            v-model="row.rate_to_cny"
            :min="0.000001"
            :max="100"
            :step="0.01"
            :decimal-places="6"
            size="small"
            style="width: 140px"
          />
        </template>
        <template #action="{ row }">
          <t-button
            size="small"
            variant="outline"
            :loading="saving === row.currency"
            @click="handleSave(row)"
          >
            保存
          </t-button>
        </template>
      </t-table>
    </t-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { listExchangeRates, updateExchangeRate } from '@/api/exchangeRates'
import type { ExchangeRateItem } from '@/api/exchangeRates'

const loading = ref(false)
const saving = ref('')
const rates = ref<ExchangeRateItem[]>([])

const rateColumns = [
  { colKey: 'currency', title: '币种', width: 100 },
  { colKey: 'rate_to_cny', title: '兑人民币汇率', width: 200, cell: 'rate_to_cny' },
  { colKey: 'action', title: '操作', width: 100, cell: 'action' },
]

async function loadRates() {
  loading.value = true
  const r = await listExchangeRates()
  loading.value = false
  if (r.ok && r.data) {
    rates.value = r.data
  }
}

async function handleSave(row: ExchangeRateItem) {
  saving.value = row.currency
  const r = await updateExchangeRate(row.currency, row.rate_to_cny)
  saving.value = ''
  if (r.ok) {
    MessagePlugin.success(`${row.currency} 汇率已更新`)
  } else {
    MessagePlugin.warning(r.error || '更新失败')
  }
}

onMounted(() => {
  loadRates()
})
</script>
