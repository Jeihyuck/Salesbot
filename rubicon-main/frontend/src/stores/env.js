import { defineStore } from 'pinia'

export const useEnvStore = defineStore('env', {
    state: () => ({
      isMobile: false,
    }),
    actions: {
    },
    persist: true,
  })