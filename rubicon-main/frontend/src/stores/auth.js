import { defineStore } from 'pinia'
import { useRouter } from 'vue-router'
import { alphaAuth, authService } from '@/_services'

export const useAuthStore = defineStore('auth', {
    state: () => ({
      router: useRouter(),
      // Bypass auth in development when VITE_OP_TYPE=DEV or VITE_BYPASS_AUTH=true
      isAuthenticated: (import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.VITE_OP_TYPE === 'DEV') ? true : false,
      username: (import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.VITE_OP_TYPE === 'DEV') ? (import.meta.env.VITE_BYPASS_USERNAME || 'debug') : null,
      department: (import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.VITE_OP_TYPE === 'DEV') ? (import.meta.env.VITE_BYPASS_DEPARTMENT || 'dev') : null,
      group: (import.meta.env.VITE_BYPASS_AUTH === 'true' || import.meta.env.VITE_OP_TYPE === 'DEV') ? (import.meta.env.VITE_BYPASS_GROUP ? JSON.parse(import.meta.env.VITE_BYPASS_GROUP) : null) : null,
      refreshToken: null,
      accessToken: null,
      accessTokenIssueTime: null
    }),
    actions: {
      updateLogout() {
        this.isAuthenticated = false
        this.username = null
        this.department = null
        this.group = null
        this.refreshToken = null
        this.accessToken = null
        this.accessTokenIssueTime = null
      },
      async login (username, password, mfaCode, siteID) {
        // console.log('pinia login called')
        await alphaAuth.login.login(username, password, mfaCode, siteID)
          .then((response) => {
              if (response.success) {
                this.isAuthenticated = true
                this.username = response.user.username,
                this.department = response.user.department,
                this.group = response.user.group,
                this.refreshToken = response.refreshToken,
                this.accessToken = response.accessToken,
                this.accessTokenIssueTime = new Date()
                this.router.push('/chat') //
              } else {
                this.updateLogout()
                // app.config.globalProperties.$snackbar.showSnackbar({
                //   title: 'Incorrect Login',
                //   message: 'Login infomation is not correct, check your ID and Password',
                //   color: 'error',
                //   timeout: 3000,
                // })
              }
            })
      },
      async logout () {
        authService.logout()
        this.router.push('/')
        this.updateLogout()
      },
      async inspectAccessTokenHeader () {
        // console.log('Check Token')
        const nowTime = new Date()
        // let accessToken = this.accessToken
        // console.log(this.accessToken)
        const accessTokenIssueTime = Date.parse(this.accessTokenIssueTime)
        // console.log(accessTokenIssueTime)
        if (isNaN(accessTokenIssueTime)) {
          this.updateLogout()
        } else {
          const refreshToken = this.refreshToken
          const seconds = (nowTime.getTime() - accessTokenIssueTime) / 1000
          if (seconds >= 560) { // 580 seconds will be good enough.'
            // console.log('accessToken has expired. New Token will be taken')
            await authService.refreshAccessToken(refreshToken)
              .then(token => {
                // accessToken =
                // // console.log(accessToken)
                // const payload = { accessToken: accessToken }
                this.accessToken = token.access
                this.accessTokenIssueTime = new Date()
              }).catch(error => {
                console.log(error)
                this.updateLogout()
              })
          }
        }
      }
    },
    persist: true,
  })
