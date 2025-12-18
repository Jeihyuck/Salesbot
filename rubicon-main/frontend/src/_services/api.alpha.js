import { serviceAlpha } from '@/_services/index'

const menuAPI = 'api/alpha/menu/'
const menu = {
  // getUserMenus: () => {
  //   return serviceAlpha.stdPostFunction(
  //     menuAPI,
  //     {
  //       action: 'getUserMenuList',
  //       query: {}
  //     }
  //   )
  // },
  getMenuList: () => {
    return serviceAlpha.stdPostFunction(
      menuAPI,
      {
        action: 'get_menu_list',
        query: {}
      }
    )
  }
}

const tableAPI = 'api/alpha/table/'
const table = {
  getTableHeader: (tableID) => {
    const query = {
      id: tableID
    }
    return serviceAlpha.stdPostFunction(
      tableAPI,
      {
        action: 'get_table_header',
        query: query
      }
    )
  }
}

const apiAPI = 'api/alpha/api/'
const api = {
  getAPIList: () => {
    return serviceAlpha.stdPostFunction(
      apiAPI,
      {
        action: 'getAPIList',
        query: {}
      }
    )
  }
}

const utilAPI = 'api/alpha/util/'
const util = {
  excelDownload: (jobUUID, requestURL, requestAction, requestQuery, excelTemplateName) => {
    const query = {
      jobUUID: jobUUID,
      url: requestURL,
      action: requestAction,
      query: requestQuery,
      template: excelTemplateName,
      paging: {
        page: 1,
        itemsPerPage: 10000
      }
    }
    return serviceAlpha.stdPostFunction(
      utilAPI,
      {
        action: 'excel_download',
        query: query
      }
    )
  },
  wait: (seconds) => {
    const query = {
      seconds: seconds
    }
    return serviceAlpha.stdPostFunction(
      utilAPI,
      {
        action: 'wait',
        query: query
      }
    )
  }
}

const grpcAPI = 'api/alpha/grpc/'
const grpc = {
  grpcCall: (jobUUID, requestGrpcServer, requestGrpcFunction, question) => {
    const query = {
      jobUUID: jobUUID,
      human: question
    }
    return serviceAlpha.stdPostFunction(
      grpcAPI + '/' + requestGrpcServer + '/' + requestGrpcFunction + '/',
      {
        action: 'answer',
        query: query
      }
    )
  }
}

export const alpha = {
  menu: menu,
  table: table,
  api: api,
  util: util,
  grpc: grpc
}
