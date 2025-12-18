import { serviceAlpha } from '@/_services/index'

const serviceAPI = 'api/log/service/'
const service = {
  logService: (service, serviceQuery) => {
    const query = {
      service: service,
      serviceQuery: serviceQuery
    }
    return serviceAlpha.stdPostFunction(
      serviceAPI,
      {
        action: 'logService',
        query: query
      }
    )
  }
}

const statsAPI = 'api/log/stats/'
const stats = {
  getLoginStat: (startDate, endDate) => {
    const query = {
      startDate: startDate,
      endDate: endDate
    }
    return serviceAlpha.stdPostFunction(
      statsAPI,
      {
        action: 'getLoginStat',
        query: query
      }
    )
  },
  getLoginList: (startDate, endDate) => {
    const query = {
      startDate: startDate,
      endDate: endDate
    }
    return serviceAlpha.stdPostFunction(
      statsAPI,
      {
        action: 'getLoginList',
        query: query
      }
    )
  },
  getServiceStats: (startDate, endDate) => {
    const query = {
      startDate: startDate,
      endDate: endDate
    }
    return serviceAlpha.stdPostFunction(
      statsAPI,
      {
        action: 'getServiceStats',
        query: query
      }
    )
  },
  getAPIStats: (startDate, endDate) => {
    const query = {
      startDate: startDate,
      endDate: endDate
    }
    return serviceAlpha.stdPostFunction(
      statsAPI,
      {
        action: 'getAPIStats',
        query: query
      }
    )
  }
}

const kakaoAPI = 'api/log/read_kakao_log/'
const kakao = {
  getKakaoLog: (logId) => {
    return serviceAlpha.stdPostFunction(
      kakaoAPI,
      {
        action: 'readLog',
        query: {
          logId: logId
        }
      }
    )
  }
}

export const alphaLog = {
  service: service,
  stats: stats,
  kakao: kakao
}
