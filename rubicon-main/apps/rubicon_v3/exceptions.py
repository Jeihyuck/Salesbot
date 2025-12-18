from rest_framework.exceptions import APIException
from rest_framework import status


class PayloadTooLargeException(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "File size too large"
    default_code = "payload_too_large"


class InvalidFileTypeException(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Invalid file type"
    default_code = "invalid_file_type"


class TooManyFilesException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Too many files"
    default_code = "too_many_files"


class TotalSizeTooLargeException(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "Total file size too large"
    default_code = "total_size_too_large"


class InvalidImageResolutionException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid image resolution"
    default_code = "invalid_resolution"
