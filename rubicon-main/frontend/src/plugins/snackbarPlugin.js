import { useSnackbarStore } from '@/stores/snackbar'

export default {
  install(app, options) {
    const snackbar = useSnackbarStore()
    app.config.globalProperties.$snackbar = snackbar
  },
};