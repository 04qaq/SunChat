import { createRouter, createWebHashHistory } from 'vue-router'

import AppHome from './views/AppHome.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [{ path: '/', name: 'home', component: AppHome }],
})
