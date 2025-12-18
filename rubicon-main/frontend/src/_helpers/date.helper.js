import { zfill } from '@/_helpers'

export function dateParse (str) {
  var y = parseInt(str.substr(0, 4))
  var m = parseInt(str.substr(5, 2)) - 1
  var d = parseInt(str.substr(8, 2))
  return new Date(y, m, d)
}

export function datetimeParse (str) {
  // const str = '09/24/2022 07:30:14';

  // 2022-05-01 00:01:00

  let [dateValues, timeValues] = str.split(' ')
  if (timeValues.length === 5) {
    timeValues = timeValues + ':00'
  }

  const [year, month, day] = dateValues.split('-')
  const [hours, minutes, seconds] = timeValues.split(':')

  const datetime = new Date(year, month - 1, day, hours, minutes, seconds)
  return datetime
}

export function getToday () {
  var date = new Date()
  // var year = date.getFullYear()
  // var month = ('0' + (1 + date.getMonth())).slice(-2)
  // var day = ('0' + date.getDate()).slice(-2)
  const year = date.getFullYear()
  const month = zfill(date.getMonth() + 1, 2)
  const day = zfill(date.getDate(), 2)
  return year + '-' + month + '-' + day
}

export function getNMonthBeforeDate (numOfMonths, date = new Date()) {
  date.setMonth(date.getMonth() - numOfMonths)
  const year = date.getFullYear()
  const month = zfill(date.getMonth() + 1, 2)
  const day = zfill(date.getDate(), 2)
  return year + '-' + month + '-' + day
}

export function getMonth () {
  var date = new Date()
  var year = date.getFullYear()
  var month = ('0' + (1 + date.getMonth())).slice(-2)

  return year + '-' + month
}

export function toStringByFormatting (date, delimiter = '-') {
  const year = date.getFullYear()
  const month = zfill(date.getMonth() + 1, 2)
  const day = zfill(date.getDate(), 2)
  // console.log(year, month, day)
  return [year, month, day].join(delimiter)
}

function koreanWeekDay (weekday) {
  if (weekday === 0) {
    return 6
  } else {
    return weekday - 1
  }
}

export function getFirstLastWeekDayOfToday () {
  var curr = new Date()
  var first = curr.getDate() - koreanWeekDay(curr.getDay())
  var last = first + 6

  var firstday = toStringByFormatting(new Date(curr.setDate(first)))
  var lastday = toStringByFormatting(new Date(curr.setDate(last)))
  return { firstday: firstday, lastday: lastday }
}

export function getDatetimeString (date) {
  var yyyy = date.getFullYear().toString()
  var MM = zfill(date.getMonth() + 1, 2)
  var dd = zfill(date.getDate(), 2)
  var hh = zfill(date.getHours(), 2)
  var mm = zfill(date.getMinutes(), 2)
  var ss = zfill(date.getSeconds(), 2)

  return yyyy + '-' + MM + '-' + dd + ' ' + hh + ':' + mm + ':' + ss
}

export function addMinutes (date, minutes) {
  return new Date(date.getTime() + minutes * 60000)
}

export function getDatetimeStringFromString (datetimeString) {
  return datetimeString.substring(0, 19).replace('T', ' ')
}
