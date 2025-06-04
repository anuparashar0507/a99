from typing import Optional


class RepositoryException(Exception):
    """
    Base exception for repository errors.
    Accepts the repository name and an optional original exception.
    """

    def __init__(
        self,
        repo_name: str,
        message: str,
        original_exception: Optional[Exception] = None,
    ):
        self.repo_name = repo_name
        self.original_exception = original_exception
        full_message = f"[{repo_name}] {message}"
        if original_exception:
            full_message += f" | Original error: {original_exception}"
        super().__init__(full_message)


class RepositoryCreateException(RepositoryException):
    """
    Raised when creating a record fails.
    """

    def __init__(self, repo_name: str, original_exception: Optional[Exception] = None):
        super().__init__(repo_name, "Failed to create record", original_exception)


class RepositoryReadException(RepositoryException):
    """
    Raised when reading a record fails.
    """

    def __init__(self, repo_name: str, original_exception: Optional[Exception] = None):
        super().__init__(repo_name, "Failed to read record", original_exception)


class RepositoryUpdateException(RepositoryException):
    """
    Raised when updating a record fails.
    """

    def __init__(self, repo_name: str, original_exception: Optional[Exception] = None):
        super().__init__(repo_name, "Failed to update record", original_exception)


class RepositoryDeleteException(RepositoryException):
    """
    Raised when deleting a record fails.
    """

    def __init__(self, repo_name: str, original_exception: Optional[Exception] = None):
        super().__init__(repo_name, "Failed to delete record", original_exception)


class RepositoryNotFoundException(RepositoryException):
    """
    Raised when a record is not found in the repository.
    """

    def __init__(
        self,
        repo_name: str,
        identifier: str,
        original_exception: Optional[Exception] = None,
    ):
        message = f"Record with identifier '{identifier}' not found"
        super().__init__(repo_name, message, original_exception)
