import { createRouter, createWebHistory } from 'vue-router'

const PersonDetail = () => import('@/pages/PersonDetail.vue')

const routes = [
  { path: '/', name: 'Home', component: () => import('@/pages/Home.vue') },
  { path: '/clients', name: 'Clients', component: () => import('@/pages/Clients.vue') },
  { path: '/leads', name: 'Leads', component: () => import('@/pages/Leads.vue') },
  { path: '/chat', name: 'Chat', component: () => import('@/pages/Chat.vue') },
  { path: '/settings', name: 'Settings', component: () => import('@/pages/Settings.vue') },
  { path: '/onboarding', name: 'Onboarding', component: () => import('@/pages/Onboarding.vue') },

  // Unified Person detail — accepts any of lead/deal/contact id
  { path: '/person/:id', name: 'PersonDetail', component: PersonDetail, props: true },

  // Aliases (no client-side redirect; same component, identity resolved client-side)
  { path: '/leads/:id', name: 'LeadDetail', component: PersonDetail, props: true },
  { path: '/clients/:id', name: 'ClientDetail', component: PersonDetail, props: true },
  { path: '/deals/:id', name: 'DealDetail', component: PersonDetail, props: true },
  { path: '/contacts/:id', name: 'ContactDetail', component: PersonDetail, props: true },

  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('@/pages/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory('/booncrm'),
  routes,
})

export default router
