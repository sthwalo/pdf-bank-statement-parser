"""Custom exceptions specific to this project"""


class OutputInvalidException(Exception):
    """Exception raised when process is unable to generate valid output"""


class ValidationTestFailedException(Exception):
    "Exception raised when a validation check fails"
    pass
