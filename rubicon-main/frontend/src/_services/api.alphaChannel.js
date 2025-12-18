// // import { subdomainPrefix } from '@/settings.js'
// import ReconnectingWebSocket from 'reconnecting-websocket'

// export const alphaChannel = {
//   createChannel
// }

// function createChannel (uuid, callbackFunction) {
//   let connectionHost = ''
//   uuid = uuid.replace(/-/g, '')

//   connectionHost = import.meta.env.VITE_WS_URL
//   // console.log('channel Connection Host : ' + connectionHost)

//   const options = {
//     // maxReconnectionDelay: 10000,
//     maxReconnectionDelay: 60000,
//     minReconnectionDelay: 1000 + Math.random() * 4000,
//     reconnectionDelayGrowFactor: 1.3,
//     minUptime: 5000,
//     // connectionTimeout: 4000,
//     connectionTimeout: 60000,
//     maxRetries: Infinity,
//     maxEnqueuedMessages: Infinity,
//     startClosed: false,
//     debug: false
//   }

//   const channelSocket = new ReconnectingWebSocket(
//     connectionHost + import.meta.env.VITE_PUBLIC_PATH.concat('api/ws/channel/') + uuid + '/',
//     [],
//     options
//   )

//   channelSocket.onmessage = function (messageEvent) {
//     // console.log('messageEvent', messageEvent)
//     const messageEventData = JSON.parse(messageEvent.data).message
//     callbackFunction(messageEventData)
//   }

//   channelSocket.onopen = function (e) {
//     console.log('Socket opened.', e.target.url)
//   }

//   channelSocket.onclose = function (e) {
//     console.log('Socket closed.', e.reason)
//   }

//   channelSocket.onerror = function (err) {
//     console.error('Socket encountered error: ', err.message, 'Closing socket')
//     channelSocket.close()
//   }

//   return channelSocket
// }
