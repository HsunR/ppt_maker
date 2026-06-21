import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import { store } from './api'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/input', name: 'input', component: () => import('./views/InputView.vue'), meta: { requiresProject: true } },
  { path: '/outline', name: 'outline', component: () => import('./views/OutlineView.vue'), meta: { requiresProject: true } },
  { path: '/style', name: 'style', component: () => import('./views/StyleView.vue'), meta: { requiresProject: true } },
  { path: '/confirm', name: 'confirm', component: () => import('./views/ConfirmView.vue'), meta: { requiresProject: true } },
  { path: '/progress', name: 'progress', component: () => import('./views/ProgressView.vue'), meta: { requiresProject: true } },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresProject && !store.currentProject?.id) {
    next('/')
  } else {
    next()
  }
})

export default router