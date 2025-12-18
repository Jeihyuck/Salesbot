class HttpStatus:
    def __init__(self):
        self.status = 200


class BaseCustomException(Exception):
    """Base class for custom exceptions"""

    status_code = None

    def __init__(self, message, error_code=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code

    def __str__(self):
        if self.error_code is not None:
            return f"[Error {self.error_code}]: {self.message}"
        return self.message


class ProcessTimeout(BaseCustomException):
    """A custom exception for job timeouts"""

    status_code = 408


class ProcessError(BaseCustomException):
    """A custom exception for job errors"""

    status_code = 500


class InformationRestrictedException(BaseCustomException):
    """A custom exception for restricted information"""

    status_code = 422


class InvalidOriginalQuery(BaseCustomException):
    """A custom exception for invalid original queries"""

    status_code = 451


class InvalidCodeMapping(BaseCustomException):
    """A custom exception for invalid code mappings"""

    status_code = 200


class MultipleInputException(BaseCustomException):
    """A custom exception for multiple inputs"""

    status_code = 204


class InvalidStore(BaseCustomException):
    """A custom exception for invalid store information"""

    status_code = 200


class EmptyStreamData(BaseCustomException):
    """A custom exception for empty stream data"""

    status_code = 200


class EmptyOriginalQuery(BaseCustomException):
    """A custom exception for empty original queries"""

    status_code = 200


class PreEmbargoQueryException(BaseCustomException):
    """A custom exception for pre-embargo queries"""

    status_code = 200


class RedirectRequestException(BaseCustomException):
    """A custom exception for redirect requests"""

    status_code = 202


class NoDataFoundException(BaseCustomException):
    """A custom exception for no data found"""

    status_code = 200


class RewriteCorrectionFailureException(BaseCustomException):
    """A custom exception for rewrite correction failures"""

    status_code = 200


class ResponseGenerationFailureException(BaseCustomException):
    """A custom exception for response generation failures"""

    status_code = 500
