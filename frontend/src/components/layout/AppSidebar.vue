<template>
  <t-menu :value="activeKey" theme="light" style="height: 100%; border-right: 1px solid var(--td-component-stroke);">
    <template #logo>
      <div class="px-4 py-4 text-lg font-bold text-gray-800">StockMemos</div>
    </template>
    <t-menu-item value="dashboard" @click="go('/')">
      <template #icon><t-icon name="chart-bar" /></template>
      持仓总览
    </t-menu-item>
    <t-menu-item value="capital" @click="go('/capital')">
      <template #icon><t-icon name="money" /></template>
      资金管理
    </t-menu-item>
    <t-menu-item value="memos" @click="go('/memos')">
      <template #icon><t-icon name="file" /></template>
      投资备忘
    </t-menu-item>
    <t-menu-item value="settings" @click="go('/settings')">
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
  if (route.path.startsWith('/capital')) return 'capital'
  if (route.path.startsWith('/memos')) return 'memos'
  if (route.path.startsWith('/settings')) return 'settings'
  return 'dashboard'
})

function go(path: string) {
  router.push(path)
}
</script>
