// import { getCurrentInstance } from 'vue'
import app from '@/main'
import axios from 'axios'
import store from '@/stores'
import { getAccessToken } from '@/_helpers'

// const { proxy } = getCurrentInstance()

export const serviceAlpha = {
  stdPostFunction,
  getFile
}
async function stdPostFunction (url, params, json=false, apiKey = null) {
  if (json) {
    return stdPostFunctionJson(url, params, apiKey)
  } else {
    return stdPostFunctionFormData(url, params, apiKey)
  }
}

async function stdPostFunctionJson (url, params, apiKey = null) {
  let isValid = true
  let axiosConfig = {}

  if (apiKey !== null) {
    const authCode = 'Api-Key ' + apiKey
    axiosConfig = {
      headers: {
        'Content-Type': 'application/json',
        Authorization: authCode
      }
    }
  } else {
    const accessToken = await getAccessToken()

    if (accessToken === 'NotAvailable') {
      axiosConfig = {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    } else {
      axiosConfig = {
        headers: {
          'Content-Type': 'application/json',
          Authorization: accessToken
        }
      }
    }
  }

  if (isValid) {
    return axios.post(import.meta.env.VITE_PUBLIC_PATH.concat(url), params, axiosConfig)
      .then(response => {
        if ('msg' in response.data && response.data.msg !== null && !('error' in response.data)) {
          if (!response.data.msg.type || !response.data.msg.title || !response.data.msg.text) {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: 'Backend Error',
              message: 'The format of the message sent from the backend is incorrect.',
              color: 'error',
              timeout: 3000,
            }) 
          } else {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: response.data.msg.title,
              message: response.data.msg.text,
              color: response.data.msg.type,
              timeout: 3000,
            })
          }
        } else if ('error' in response.data) {
          if (import.meta.env.VITE_OP_TYPE === 'DEV') {
            console.log('DEV Error')
            // store.dispatch('backendError/showBackendError', response.data.error.join('\n'))
          } else {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: 'Backend Error',
              message: 'Backend Service Error',
              color: 'error',
              timeout: 3000,
            })
          }
        }
        return response.data
      })
      .catch(e => {
        console.log(e)
      })
  } else {
    return Promise.resolve().then(() => {
      return { success: false }
    })
  }
}

async function stdPostFunctionFormData (url, params, apiKey = null) {
  const formData = new FormData()
  let isValid = true

  for (var key in params) {
    if (key === 'query') {
      formData.append('query', JSON.stringify(params.query))
    } else if (key === 'paging') {
      formData.append('paging', JSON.stringify(params.paging))
    } else if (key === 'files') {
      for (let i = 0; i < params.files.length; i++) {
        formData.append('files', params.files[i].file)
      }
    } else {
      formData.append(key, params[key])
    }
  }

  let axiosConfig = {}

  if (apiKey !== null) {
    const authCode = 'Api-Key ' + apiKey
    axiosConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: authCode
      }
    }
  } else {
    const accessToken = await getAccessToken()

    if (accessToken === 'NotAvailable') {
      axiosConfig = {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    } else {
      axiosConfig = {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: accessToken
        }
      }
    }
  }

  if (isValid) {
    return axios.post(import.meta.env.VITE_PUBLIC_PATH.concat(url), formData, axiosConfig)
      .then(response => {
        if ('msg' in response.data && response.data.msg !== null && !('error' in response.data)) {
          if (!response.data.msg.type || !response.data.msg.title || !response.data.msg.text) {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: 'Backend Error',
              message: 'The format of the message sent from the backend is incorrect.',
              color: 'error',
              timeout: 3000,
            }) 
          } else {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: response.data.msg.title,
              message: response.data.msg.text,
              color: response.data.msg.type,
              timeout: 3000,
            })
          }
        } else if ('error' in response.data) {
          if (import.meta.env.VITE_OP_TYPE === 'DEV') {
            console.log('DEV Error')
            // store.dispatch('backendError/showBackendError', response.data.error.join('\n'))
          } else {
            app.config.globalProperties.$snackbar.showSnackbar({
              title: 'Backend Error',
              message: 'Backend Service Error',
              color: 'error',
              timeout: 3000,
            })
          }
        }
        return response.data
      })
      .catch(e => {
        console.log(e)
      })
  } else {
    return Promise.resolve().then(() => {
      return { success: false }
    })
  }
}

async function getFile (fileID, fileName) {
  const accessToken = await getAccessToken()
  const axiosConfig = {
    responseType: 'arraybuffer',
    headers: {
      'Content-Type': 'application/json',
      Authorization: accessToken
    }
  }

  return axios.get(import.meta.env.VITE_PUBLIC_PATH.concat('api/alpha/file/get/') + fileID + '/', axiosConfig)
    .then((response) => {
      var fileURL = window.URL.createObjectURL(new Blob([response.data]))
      var fileLink = document.createElement('a')

      fileLink.href = fileURL
      fileLink.setAttribute('download', fileName)
      document.body.appendChild(fileLink)

      fileLink.click()
    })
    .catch(e => {
      console.log(e)
    })
}
