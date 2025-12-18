import Vue from 'vue'
import axios from 'axios'
import { GraphQLClient } from 'graphql-request'
import { getAccessToken, checkSpecialCharacter } from '@/_helpers'

export const serviceAlpha = {
  stdPostFunction,
  stdGraphQLFunction,
  getFile
}

function validation (key, obj, dataFormat) {
  let valid = true
  if (key in dataFormat) {
    // console.log(key, 'key is in dataFormat', dataFormat[key].format) // perform your operation on the value
    if (dataFormat[key].format.includes('NUMBER')) {
      // console.log('Check if NUMBER')
      // console.log(isNaN(obj))
      if (isNaN(obj)) {
        Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: dataFormat[key].text + ' ' + '숫자가 입력되어야 합니다.' })
      }
    }
    if (dataFormat[key].format.includes('POSITIVE_NUMBER')) {
      // console.log('Check if POSITIVE_NUMBER')
      // console.log(isNaN(obj))
      if (isNaN(obj)) {
        Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: dataFormat[key].text + ' ' + '양수가 입력되어야 합니다.' })
        valid = false
      } else {
        if (parseInt(obj) < 0) {
          Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: dataFormat[key].text + ' ' + '양수가 입력되어야 합니다.' })
          valid = false
        }
      }
    }
    if (dataFormat[key].format.includes('NEGATIVE_NUMBER')) {
      if (isNaN(obj)) {
        Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: dataFormat[key].text + ' ' + '음수가 입력되어야 합니다.' })
        valid = false
      } else {
        if (parseInt(obj) > 0) {
          Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: dataFormat[key].text + ' ' + '음수가 입력되어야 합니다.' })
          valid = false
        }
      }
    }
  }
  // Check common format
  if (typeof obj === 'string') {
    if (checkSpecialCharacter(obj)) {
      Vue.notify({ group: 'alpha', type: 'warn', title: 'Info', duration: 2000, text: '입력에 특수문자가 포함되어 있습니다.' })
      valid = false
    }
  }

  return valid
}
function iterateFormatValidation (key, obj, dataFormat) {
  let valid = true
  // console.log(key, obj, dataFormat)
  // console.log(typeof obj)
  if (typeof obj === 'object') {
    for (const key in obj) {
      const value = obj[key]
      if (typeof value === 'object') {
        valid = iterateFormatValidation(key, value, dataFormat) // recursively call the function for nested objects
      } else {
        valid = validation(key, value, dataFormat)
      }
    }
  } else {
    valid = validation(key, obj, dataFormat)
  }
  return valid
}

async function formatValidation (params) {
  // console.log(params.query)
  // console.log(params.dataFormat)
  let valid = true
  for (const [key, value] of Object.entries(params.query)) {
    if (!iterateFormatValidation(key, value, params.dataFormat)) {
      valid = false
    }
  }
  return valid
}

async function stdPostFunction (url, params) {
  const formData = new FormData()
  let fileCount = 0
  let isValid = true
  formData.append('file_count', fileCount)

  for (var key in params) {
    if (key === 'query') {
      formData.append('query', JSON.stringify(params.query))
    } else if (key === 'paging') {
      formData.append('paging', JSON.stringify(params.paging))
    } else if (key === 'file') {
      for (const index in params[key]) {
        fileCount = parseInt(index) + 1
        formData.append('file_count', fileCount)
        formData.append('file' + index, params[key][index])
      }
    } else if (key === 'dataFormat') {
      isValid = await formatValidation(params)
    } else {
      formData.append(key, params[key])
    }
  }

  axiosConfig = {
    headers: {
      'Content-Type': 'multipart/form-data',
      Authorization: 'accessToken'
    }
  }

  if (isValid) {
    return axios.post(import.meta.env.VITE_PUBLIC_PATH.concat(url), formData, axiosConfig)
      .then(response => {
        // console.log(response)
        if ('msg' in response.data && response.data.msg !== null) {
          if (!response.data.msg.type || !response.data.msg.title || !response.data.msg.text) {
            Vue.notify({
              group: 'alpha',
              type: 'error',
              title: '메시지 형식 오류',
              duration: 2000,
              text: 'Backend 에서 전달되는 메시지의 형식이 잘못되었습니다.'
            })
          } else {
            Vue.notify({
              group: 'alpha',
              type: response.data.msg.type,
              title: response.data.msg.title,
              duration: 2000,
              text: response.data.msg.text
            })
          }
        }
        // delete response.data.msg
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

async function stdGraphQLFunction (query) {
  let headers = {}

  const accessToken = await getAccessToken()
  if (accessToken === 'NotAvailable') {
    headers = {}
  } else {
    headers = {
      Authorization: accessToken
    }
  }
  const client = new GraphQLClient(import.meta.env.VITE_PUBLIC_PATH.concat('api/graphql/'), { headers: headers })

  return client.request(query)
    .then(response => {
      return response
    })
    .catch(e => {
      console.log(e)
    })
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
