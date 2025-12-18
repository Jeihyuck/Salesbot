import { defineStore } from 'pinia';

export const useSnackbarStore = defineStore('snackbar', {
  state: () => ({
    show: false,
    title: '',
    message: '',
    color: 'success', // Options: 'success', 'error', 'info', 'warning'
    timeout: 3000, // Duration in milliseconds
  }),
  actions: {
    showSnackbar({ title, message, color = 'success', timeout = 3000 }) {
      this.title = title;
      this.message = message;
      this.color = color;
      this.timeout = timeout;
      this.show = true;
    },
    closeSnackbar() {
      this.show = false;
    },
  },
});