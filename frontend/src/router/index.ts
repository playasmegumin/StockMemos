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
  ],
})

export default router
