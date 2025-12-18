export function zfill (num, len) {
  return (Array(len).join('0') + num).slice(-len)
}

export async function waitFor (conditionFunction) {
  console.log('Wait For')
  while (conditionFunction() === false) {
    await new Promise(resolve => setTimeout(resolve, 500))
  }
}

export function numberWithCommas (x) {
  if (isNaN(x)) {
    return x.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  } else {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  }
}

export function toUniqueArray (a) {
  var newArr = []
  for (var i = 0; i < a.length; i++) {
    if (newArr.indexOf(a[i]) === -1) {
      newArr.push(a[i])
    }
  }
  return newArr
}

/**
 * Function to sort alphabetically an array of objects by some specific key.
 *
 * @param {String} property Key of the object to sort.
 */
export function dynamicSort (property) {
  var sortOrder = 1

  if (property[0] === '-') {
    sortOrder = -1
    property = property.substr(1)
  }

  return function (a, b) {
    if (sortOrder === -1) {
      return b[property].localeCompare(a[property])
    } else {
      return a[property].localeCompare(b[property])
    }
  }
}

export function popItemFromArray (array, item, key) {
  let index = 0
  for (var i = 0; i < array.length; i++) {
    if (array[i][key] === item[key]) {
      array.splice(i, 1)
      index = i
    }
  }
  return [array, index]
}

export function replaceMatchingElement (array, newElement, matchingKey) {
  const index = array.findIndex(el => el[matchingKey] === newElement[matchingKey])

  if (index === -1) {
    array.push(newElement)
  } else {
    array[index] = newElement
  }
}

export function addIndexToArray (array, startNum) {
  for (var index = 0; index < array.length; index++) {
    array[index].index = index + startNum
  }
  // console.log(array)
  return array
}

export function removeFromArray (array, value) {
  return array.filter(function (element) {
    return element !== value
  })
}

export function floatToPercent (floatValue, decimalPoints) {
  let value = floatValue * 100
  value = value.toFixed(decimalPoints)
  return value.toString() + ' %'
}

export function floatToFixed (floatValue, decimalPoints) {
  return floatValue.toFixed(decimalPoints)
}

export function s2ab (s) {
  var buf = new ArrayBuffer(s.length)
  var view = new Uint8Array(buf)
  for (var i = 0; i < s.length; i++) view[i] = s.charCodeAt(i) & 0xFF
  return buf
}

export function mapTableData (tableData, dataMap) {
  for (let i = 0; i < tableData.length; i++) {
    for (const [key, value] of Object.entries(dataMap)) {
      value(
        tableData[i],
        tableData[i][key]
      )
    }
  }
  return tableData
}

// import dayjs from 'dayjs'

// export const util = {
export function commanizeNumber (number) {
  return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

export function capitalizeFirstLetter (text) {
  return text.charAt(0).toUpperCase() + text.toLowerCase().slice(1)
}
//   isLocalDev: () => { return import.meta.env.NODE_ENV === 'pwc-dev' },
//   toDate: (dtString, format = 'YYYY-MM-DD') => {
//     const dt = dayjs(dtString)
//     return dt.format(format)
//   }
// }

export function changeDictToXYList (listOfDict, xKey, yKey) {
  const xList = []
  const yList = []
  for (let i = 0; i < listOfDict.length; i++) {
    for (const [key, value] of Object.entries(listOfDict[i])) {
      if (key === xKey) {
        xList.push(value)
      }
      if (key === yKey) {
        yList.push(value)
      }
    }
  }
  return { x: xList, y: yList }
}

export function delay (time) {
  return new Promise(resolve => setTimeout(resolve, time))
}

export function sequentialRun () {
  return Promise.resolve()
}

// export function iterateObjectValues(obj) {
//   for (const key in obj) {
//     const value = obj[key]
//     if (typeof value === "object") {
//       iterateObjectValues(value) // recursively call the function for nested objects
//     } else {
//       console.log(value) // perform your operation on the value
//     }
//   }
// }

export function checkSpecialCharacter (str) {
  const specialCharacterRegex = /[@#$%^*_+=[\]{};':"\\|<>/?]+/ // regex for special characters
  // console.log(specialCharacterRegex.test(str))
  if (specialCharacterRegex.test(str)) {
    return true
  } else {
    return false
  }
}
