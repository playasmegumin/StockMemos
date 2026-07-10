import { createApp } from 'vue'
import { createPinia } from 'pinia'
import TDesign from 'tdesign-vue-next'
import 'tdesign-vue-next/es/style/index.css'
import 'virtual:uno.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(TDesign)
// Small delay to ensure CSS modules are injected before first render
requestAnimationFrame(() => app.mount('#app'))
