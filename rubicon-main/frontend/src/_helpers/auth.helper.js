// import store from '@/stores'
import { useAuthStore } from '@/stores/auth'

export async function getAccessToken () {
  let accessToken = ''
  try {
    const authStore = useAuthStore()
    authStore.inspectAccessTokenHeader()
    if (authStore.accessToken !== null) {
      accessToken = 'Bearer ' + authStore.accessToken
    } else {
      accessToken = 'NotAvailable'
    }
  } catch {
    accessToken = 'NotAvailable'
  }
  return accessToken
}

export async function getUsername () {
  const username = authStore.username
  if (username) {
    return username
  } else {
    return {}
  }
}

export function passwordStrengthChecker (password) {
  var strongPassword = new RegExp('(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9])(?=.{8,})')
  if (strongPassword.test(password)) {
    return true
  } else {
    return false
  }
}
