import { createRouter, createWebHashHistory } from 'vue-router'

import AppHome from './views/AppHome.vue'
import ChatPage from './views/ChatPage.vue'

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'home', component: AppHome },
    { path: '/chat', name: 'chat', component: ChatPage },
  ],
})
