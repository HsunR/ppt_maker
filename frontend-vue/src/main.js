import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import StatusBadge from './components/StatusBadge.vue'

const app = createApp(App)
app.use(router)
app.component('StatusBadge', StatusBadge)
app.mount('#app')