import { serviceAlpha } from '@/_services/index'

const appraisalAPI = 'api/rubicon/appraisal/'
const appraisal = {
  function: (action, query = {}, paging = {}) => {
    const functionMap = {
      ut_appraisal: 'ut_appraisal',
      get_reference_document: 'get_reference_document',
      get_debug: 'get_debug',
    }
    return serviceAlpha.stdPostFunction(
      appraisalAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}


const rubiconHelperAPI = 'api/rubicon/helper/'
const rubiconHelper = {
  function: (action, query = {}, paging = {}) => {
    const functionMap = {
      getImages: 'get_images',
      getRelatedQuestion: "get_related_question"
    }
    return serviceAlpha.stdPostFunction(
      rubiconHelperAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const supplementaryInfoAPI = 'api/rubicon/supplementaryinfo/'
const supplementaryInfo = {
  function: (action, query = {}, paging = {}) => {
    const functionMap = {
      ut_appraisal: 'ut_appraisal',
      get_reference_document: 'get_reference_document',
      get_debug: 'get_debug',
    }
    return serviceAlpha.stdPostFunction(
      appraisalAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

export const rubicon = {
  appraisal: appraisal,
  rubiconHelper: rubiconHelper,
}
