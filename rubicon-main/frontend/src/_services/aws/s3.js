export const awsS3 = {
  getMediaUrl
}

function getMediaUrl (path, uuid, extension, type) {
  if (type === '') {
    const basicUrl = 'https://alpha-static-files.s3.ap-northeast-2.amazonaws.com'
    const url = basicUrl + path + uuid + '.' + extension
    return url
  } else {
    const basicUrl = 'https://alpha-static-files.s3.ap-northeast-2.amazonaws.com'
    const url = basicUrl + path + uuid + '-' + type + '.' + extension
    return url
  }
}
