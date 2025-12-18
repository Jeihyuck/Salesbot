import { serviceAlpha } from '@/_services/index'

const apiAPI = 'api/test/backend_test/'
const api = {
  api: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'createAPITestItem',
      read: 'readAPITestItems',
      delete: 'deleteAPITestItem',
      readItem: 'readAPITestItem'
    }
    return serviceAlpha.stdPostFunction(
      apiAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  },
  backendTest: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'createAPITestItem',
      read: 'readAPITestItems',
      update: 'updateAPITestItem',
      delete: 'deleteAPITestItem',
      copy: 'copyAPITestItem',
      backendTest: 'backendTest',
      getBackendTestResult: 'getBackendTestResult',
      clearBackendTestResult: 'clearBackendTestResult',
      deleteTestResult: 'deleteTestResult',
      getCurrentBackendTestUnitNum: 'getCurrentBackendTestUnitNum'
    }
    return serviceAlpha.stdPostFunction(
      apiAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  },
  getTestUrls: () => {
    return serviceAlpha.stdPostFunction(
      apiAPI,
      {
        action: 'getTestUrls',
        query: {}
      }
    )
  },
  getTester: () => {
    return serviceAlpha.stdPostFunction(
      apiAPI,
      {
        action: 'getTester',
        query: {}
      }
    )
  }
}

const codeAPI = 'api/test/code_test/'
const code = {
  run: (code) => {
    return serviceAlpha.stdPostFunction(
      codeAPI,
      {
        action: 'run',
        query: {
          code: code
        }
      }
    )
  },
  saveToRedis: (code) => {
    return serviceAlpha.stdPostFunction(
      codeAPI,
      {
        action: 'saveToRedis',
        query: {
          code: code
        }
      }
    )
  }
}

const sqlAPI = 'api/test/sql_test/'
const sql = {
  run: (sql) => {
    return serviceAlpha.stdPostFunction(
      sqlAPI,
      {
        action: 'run',
        query: {
          sql: sql
        }
      }
    )
  },
  saveToRedis: (sql) => {
    return serviceAlpha.stdPostFunction(
      sqlAPI,
      {
        action: 'saveToRedis',
        query: {
          sql: sql
        }
      }
    )
  }
}

export const alphaTest = {
  api: api,
  code: code,
  sql: sql
}
