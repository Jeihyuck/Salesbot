import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    darkMode: true // false = light mode, true = dark mode
  }),
  actions: {
    toggleDarkMode() {
      this.darkMode = !this.darkMode
    },
    setDarkMode(value) {
      this.darkMode = value
    }
  }
})