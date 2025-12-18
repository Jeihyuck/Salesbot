/**
 * plugins/index.js
 *
 * Automatically included in `./src/main.js`
 */

// Plugins
import vuetify from './vuetify'
import pinia from '@/stores'
import router from '@/router'
import snackbarPlugin from '@/plugins/snackbarPlugin'

import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

pinia.use(piniaPluginPersistedstate)

export function registerPlugins (app) {
  app
    .use(vuetify)
    .use(router)
    .use(pinia)
    .use(snackbarPlugin)
}

// export function registerPlugins (app) {
//   app
//     .use(vuetify)
//     .use(router)
//     .use(pinia)
//     .use(snackbarPlugin)
// }
