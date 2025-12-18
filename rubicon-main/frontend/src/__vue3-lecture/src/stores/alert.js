import { defineStore } from 'pinia';

export const useAlertStore = defineStore('snackbar', {
  state: () => ({
    show: false,
    message: '',
    color: 'success',
    timeout: 3000,
  }),
  actions: {
    showAlert(payload) {
      this.message = payload.message || '';
      this.color = payload.color || 'success';
      this.timeout = payload.timeout || 3000;
      this.show = true;
    },
    hideAlert() {
      this.show = false;
    },
  },
});