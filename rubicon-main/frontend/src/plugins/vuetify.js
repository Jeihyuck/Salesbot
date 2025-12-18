import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { VDateInput } from 'vuetify/labs/VDateInput'

// import { useThemeStore } from '@/stores/theme'

export default createVuetify({
  locale: {
    // locale: 'en-CA',
  },
  components: {
    VDateInput,
  },
  theme: {
    defaultTheme: 'alphaDark', // Define your default theme
    themes: {
      alphaLight: {
        dark: false,
        colors: {
          primary: '#1976D2',
          // other colors...
        }
      },
      alphaDark: {
        dark: true, // or true, depending on whether you want a light or dark theme
        colors: {
          primary: '#2089FF', // Set your primary color here
          // secondary: '#424242', // You can also set other colors like secondary, accent, etc.
          // accent: '#82B1FF',
          error: '#EE4B2B',
          // info: '#2196F3',
          // success: '#4CAF50',
          warning: '#f0ad4e',
        },
      },
    },
  },
})

// const themeStore = useThemeStore()

// // Watch the Pinia store’s darkMode state, and update Vuetify’s global theme accordingly
// watch(
//   () => themeStore.darkMode,
//   (newVal) => {
//     vuetify.theme.global.name.value = newVal ? 'dark' : 'light'
//   },
//   { immediate: true }
// )