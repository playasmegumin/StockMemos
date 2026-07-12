import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/pages/PortfolioDashboard.vue'),
    },
    {
      path: '/stock/:id',
      name: 'stock-detail',
      component: () => import('@/pages/StockDetail.vue'),
    },
    {
      path: '/capital',
      name: 'capital',
      component: () => import('@/pages/CapitalManage.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/pages/Settings.vue'),
    },
    {
      path: '/memos',
      name: 'memos',
      component: () => import('@/pages/MemosPage.vue'),
    },
  ],
})

export default router
