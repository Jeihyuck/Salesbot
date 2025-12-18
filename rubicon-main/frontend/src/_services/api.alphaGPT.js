import { serviceAlpha } from '@/_services/index'

const chatAPI = 'api/gpt/chat/'
const chat = {
  chatFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      chat: 'chat',
      chatStream: 'chatStream',
      getModels: 'getModels'
    }
    return serviceAlpha.stdPostFunction(
      chatAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const trainingDataListAPI = 'api/gpt/data/'
const trainingDataList = {
  trainingDataListFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      // create: 'createUser',
      read: 'readTrainingDataList',
      // update: 'updateUser',
      // delete: 'deleteUser',
      getOwnersOfTrainingData: 'getOwnersOfTrainingData'
      // resetPassword: 'resetPassword',
      // getUserInfo: 'getUserInfo'
    }
    return serviceAlpha.stdPostFunction(
      trainingDataListAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const trainingTextAPI = 'api/gpt/data/'
const trainingText = {
  trainingTextFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      // create: 'createUser',
      read: 'readTrainingTextList',
      delete: 'deleteText',
      deleteTextListSearched: 'deleteTextListSearched',
      checkDataID: 'checkDataID',
      createTrainingText: 'createTrainingText'
    }
    return serviceAlpha.stdPostFunction(
      trainingTextAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

const docAPI = 'api/gpt/doc/'
const doc = {
  docFunction: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'createDoc',
      read: 'readDocList',
      update: 'updateDoc',
      updateDocInput: 'updateDocInput',
      delete: 'deleteDoc',
      updateQA: 'updateQA',
      deleteQA: 'deleteQA',
      adjustProcessed: 'adjustProcessed',
      editQA: 'editQA'
    }
    return serviceAlpha.stdPostFunction(
      docAPI,
      {
        action: functionMap[action],
        query: query,
        paging: paging
      }
    )
  }
}

export const alphaGPT = {
  chat: chat,
  trainingDataList: trainingDataList,
  trainingText: trainingText,
  doc: doc
}
