<template>
  <t-menu :value="activeKey" theme="light" style="height: 100%; border-right: 1px solid var(--td-component-stroke);">
    <template #logo>
      <div class="px-4 py-4 text-lg font-bold text-gray-800">StockMemos</div>
    </template>
    <t-menu-item value="dashboard" @click="go('/')">
      <template #icon><t-icon name="chart-bar" /></template>
      持仓总览
    </t-menu-item>
    <t-menu-item value="agent" disabled>
      <template #icon><t-icon name="robot" /></template>
      Agent 分析
    </t-menu-item>
    <t-menu-item value="settings" disabled>
      <template #icon><t-icon name="setting" /></template>
      设置
    </t-menu-item>
  </t-menu>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const activeKey = computed(() => {
  if (route.path === '/') return 'dashboard'
  return 'dashboard'
})

function go(path: string) {
  router.push(path)
}
</script>
