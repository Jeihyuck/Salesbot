/**
 * router/index.ts
 *
 * Automatic routes for `./src/pages/*.vue`
 */

// Composables
import { createRouter, createWebHistory } from 'vue-router/auto'
import { setupLayouts } from 'virtual:generated-layouts'
import { routes } from 'vue-router/auto-routes'

import { useAuthStore } from '@/stores/auth'
import { useMenuStore } from '@/stores/menu'
// console.log(routes)
// const authStore = useAuthStore()
routes.map((route) => {
  switch (route.path) {
    case '/':
      route.meta = { requiresAuth: false, showAppBar: false, showNavDrawer: false }
      break
    case '/userRegistration':
      route.meta = { requiresAuth: false, showAppBar: false, showNavDrawer: false };
      break
    case '/chat':
      route.meta = { requiresAuth: false, showAppBar: true, showNavDrawer: false, title: false };
      break
    case '/searchSummary':
      route.meta = { requiresAuth: false, showAppBar: true, showNavDrawer: false, title: false };
      break
    default:
      route.meta = { requiresAuth: false, showAppBar: true, showNavDrawer: true };
      break
  }
  return route
})

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: setupLayouts(routes),
})

// Workaround for https://github.com/vitejs/vite/issues/11804
router.onError((err, to) => {
  if (err?.message?.includes?.('Failed to fetch dynamically imported module')) {
    if (!localStorage.getItem('vuetify:dynamic-reload')) {
      // console.log('Reloading page to fix dynamic import error')
      localStorage.setItem('vuetify:dynamic-reload', 'true')
      location.assign(to.fullPath)
    } else {
      console.error('Dynamic import error, reloading page did not fix it', err)
    }
  } else {
    console.error(err)
  }
})

router.isReady().then(() => {
  localStorage.removeItem('vuetify:dynamic-reload')
})




router.beforeEach((to, from, next) => {
  // next()

  const authStore = useAuthStore()
  const menuStore = useMenuStore()
  let menuList = []

  let hasPermission = false
  menuList = JSON.parse(JSON.stringify(menuStore.menuList))
  for (let i = 0; i < menuList.length; i++) {
    if (menuList[i].url === to.path) {
      hasPermission = true
    }
  }

  if (to.path === '/') {
    hasPermission = true
  }

  // if (to.path === '/data/webCache') {
  //   hasPermission = true
  // }

  if (to.path === '/chat') {
    hasPermission = true
  }

  if (to.path === '/searchSummary') {
    hasPermission = true
  }

  if (import.meta.env.VITE_OP_TYPE === 'DEV' && to.path === '/test') {
    hasPermission = true
  }

  if (to.path === '/userRegistration') {
    hasPermission = true
  }


  console.log('hasPermission', hasPermission)
  if (hasPermission) {
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      if (!authStore.isAuthenticated) {
        console.log('not logged in redirect to index')
      } else {
        next()
      }
    } else {
      next()
    }
  } else {
    console.log('no permission to access this page', to.path)
  }
});


export default router
