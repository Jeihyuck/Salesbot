import axios from 'axios'
import router from '../router'
// import { api } from '@/_services'

async function init () {
  localStorage.removeItem('username')
  localStorage.removeItem('refreshToken')
  localStorage.removeItem('accessToken')
  localStorage.removeItem('accessTokenIssueTime')
}


async function logout () {
  // localStorage.removeItem('username')
  // localStorage.removeItem('refreshToken')
  // localStorage.removeItem('accessToken')
  // localStorage.removeItem('accessTokenIssueTime')
}

function refreshAccessToken (refreshToken) {
  // console.log('refreshAccessToken function has been called')
  const postData = {
    refresh: refreshToken
  }

  const axiosConfig = {
    headers: {
      'Content-Type': 'application/json'
    }
  }

  return axios.post(import.meta.env.VITE_PUBLIC_PATH.concat('api/auth/token/refresh/'), postData, axiosConfig)
    .then(response => {
      if (response.data) {
        return response.data
      } else {
        router.push({ name: 'login' })
        location.reload()
      }
    })
    .catch(e => {
      console.log(e)
      return false
    })
}

async function handleResponse (response) {
  if (response.statusText !== 'OK') {
    if (response.status === 401) {
      // auto logout if 401 response returned from api
      logout()
      // location.reload(true)
    }
  } else {
    // store user details and jwt token in local storage to keep user logged in between page refreshes
    return response
  }
}

export const authService = {
  init,
  // login,
  logout,
  handleResponse,
  refreshAccessToken
}
