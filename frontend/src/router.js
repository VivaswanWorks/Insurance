import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
  },
  {
    path: '/policies',
    name: 'Policies',
    component: () => import('@/pages/Policies.vue'),
  },
  {
    path: '/policies/:name',
    name: 'PolicyDetail',
    component: () => import('@/pages/PolicyDetail.vue'),
  },
  {
    path: '/claims',
    name: 'Claims',
    component: () => import('@/pages/Claims.vue'),
  },
  {
    path: '/claims/new',
    name: 'ClaimNew',
    component: () => import('@/pages/ClaimNew.vue'),
  },
]

let router = createRouter({
  history: createWebHistory('/insurance_core'),
  routes,
})

export default router
