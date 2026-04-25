import { createApp } from 'vue'
import 'virtual:uno.css'
import '@unocss/reset/tailwind.css'

import App from './App.vue'
import { router } from './router'

import './styles/base.css'

createApp(App).use(router).mount('#app')
