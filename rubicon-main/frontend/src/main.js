import App from './App.vue'
import { createApp } from 'vue'
import { ResizeObserver } from 'vue3-resize'
import { registerPlugins } from '@/plugins'
import { useThemeStore } from '@/stores/theme'
import AsyncComputed from 'vue-async-computed'
import vuetify from '@/plugins/vuetify'
import ShortKey from 'vue3-shortkey'

const app = createApp(App)
registerPlugins(app)


app.component('resize-observer', ResizeObserver)
app.use(AsyncComputed)
app.use(ShortKey)

export default app

app.mount('#app')

const themeStore = useThemeStore()

// Watch the Pinia store’s darkMode state, and update Vuetify’s global theme accordingly
watch(
  () => themeStore.darkMode,
  (newVal) => {
    vuetify.theme.global.name.value = newVal ? 'alphaDark' : 'alphaLight'
  },
  { immediate: true }
)