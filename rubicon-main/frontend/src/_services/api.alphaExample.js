import { serviceAlpha } from '@/_services/index'

const ex12API = 'api/example/ex12/'
const ex12 = {
  ex12Function: (action, query = {}, paging = {}) => {
    const functionMap = {
      create: 'createIngredient',
      read: 'readIngredients',
      update: 'updateIngredient',
      delete: 'deleteIngredient'
    }
    const dataFormat = {
      calory: {
        text: '칼로리 값은 ',
        format: ['POSITIVE_NUMBER']
      }
    }
    return serviceAlpha.stdPostFunction(
      ex12API,
      {
        action: functionMap[action],
        query: query,
        dataFormat: dataFormat,
        paging: paging
      }
    )
  }
}

export const alphaExample = {
  ex12: ex12
}
