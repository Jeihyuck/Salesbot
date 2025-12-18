import { serviceAlpha } from '@/_services/index'

const miscAPI = 'api/auth/misc/'
const misc = {
  mfa: (username, password, siteID) => {
    const query = {
      username: username,
      password: password
    }
    return serviceAlpha.stdPostFunction(
      miscAPI,
      {
        action: 'mfa',
        query: query
      }
    )
  },
  getOneTimeSalt: (username) => {
    const query = {
      username: username
    }
    return serviceAlpha.stdPostFunction(
      miscAPI,
      {
        action: 'get_one_time_salt',
        query: query
      }
    )
  }
}

const loginAPI = 'api/auth/login/'
const login = {
  login: (username, password, mfaCode, siteID) => {
    const query = {
      username: username,
      password: password,
      mfa_code: mfaCode,
      siteID: siteID
    }
    return serviceAlpha.stdPostFunction(
      loginAPI,
      {
        action: 'login',
        query: query
      }
    )
  }
}

const accountAPI = 'api/auth/account/'
const account = {
  userFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      create_user: 'create_user',
      // read: 'getUserList',
      // update: 'updateUser',
      // delete: 'deleteUser',
      // changePassword: 'changePassword',
      // resetPassword: 'resetPassword',
      // getUserInfo: 'getUserInfo'
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  },
  roleFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'createRole',
      read: 'getRoleList',
      update: 'updateRole',
      delete: 'deleteRole'
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  },
  getMenuPermissions: (id, uuid) => {
    const query = {
      _id: id,
      table_uuid: uuid
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: 'getMenuPermission',
        query: query
      }
    )
  },
  getTablePermissions: (id, uuid) => {
    const query = {
      _id: id,
      id: uuid
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: 'getTablePermission',
        query: query
      }
    )
  },
  getObjectPermissions: (id, uuid) => {
    const query = {
      _id: id,
      objectUUID: uuid
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: 'getObjectPermission',
        query: query
      }
    )
  },
  updateRolePermissions: (id, menu, table, object) => {
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: 'updatePermissionByRole',
        query: {
          _id: id,
          menuList: menu,
          tableList: table,
          objectList: object
        }
      }
    )
  },
  checkCustomPermission: (checkPermissionType, objectUUID) => {
    const query = {
      checkPermissionType: checkPermissionType,
      objectUUID: objectUUID
    }
    return serviceAlpha.stdPostFunction(
      accountAPI,
      {
        action: 'checkCustomPermission',
        query: query
      }
    )
  }
}


const metaAPI = 'api/auth/meta/'
const meta = {
  department: (action, query = {}, paging = {}) => {
    const functionMap = {
      listDepartment: 'list_department',
      // read: 'getUserList',
      // update: 'updateUser',
      // delete: 'deleteUser',
      // changePassword: 'changePassword',
      // resetPassword: 'resetPassword',
      // getUserInfo: 'getUserInfo'
    }
    return serviceAlpha.stdPostFunction(
      metaAPI,
      {
        action: functionMap[action],
        query: query
      }
    )
  }
}

export const alphaAuth = {
  login: login,
  account: account,
  meta: meta,
  misc: misc
}
