import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/input', name: 'input', component: () => import('./views/InputView.vue') },
  { path: '/outline', name: 'outline', component: () => import('./views/OutlineView.vue') },
  { path: '/style', name: 'style', component: () => import('./views/StyleView.vue') },
  { path: '/confirm', name: 'confirm', component: () => import('./views/ConfirmView.vue') },
  { path: '/progress', name: 'progress', component: () => import('./views/ProgressView.vue') },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})