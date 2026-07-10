<template>
  <div class="app-layout grid grid-cols-[220px_1fr] h-screen">
    <AppSidebar />
    <main class="overflow-auto p-6 h-full min-h-0">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.app-layout {
  background: #f5f7fa;
}
</style>
