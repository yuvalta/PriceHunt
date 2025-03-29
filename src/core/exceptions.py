class AppException(Exception):
    """Base exception for the application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class APIError(AppException):
    """Exception for API-related errors"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)

class ValidationError(AppException):
    """Exception for validation errors"""
    def __init__(self, message: str):
        super().__init__(message, 400)

class NotFoundError(AppException):
    """Exception for not found errors"""
    def __init__(self, message: str):
        super().__init__(message, 404)

class AuthenticationError(AppException):
    """Exception for authentication errors"""
    def __init__(self, message: str):
        super().__init__(message, 401)

class AuthorizationError(AppException):
    """Exception for authorization errors"""
    def __init__(self, message: str):
        super().__init__(message, 403) 