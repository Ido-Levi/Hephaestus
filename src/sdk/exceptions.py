"""Custom exceptions for the Hephaestus SDK."""


class HephaestusError(Exception):
    """Base exception for all Hephaestus SDK errors."""

    pass


class HephaestusStartupError(HephaestusError):
    """Raised when Hephaestus fails to start within the timeout period."""

    pass


class SDKNotRunningError(HephaestusError):
    """Raised when attempting operations on a non-running SDK instance."""

    pass


class InvalidPhaseError(HephaestusError):
    """Raised when an invalid phase ID is referenced."""

    pass


class TaskCreationError(HephaestusError):
    """Raised when task creation fails on the backend."""

    pass


class TaskNotFoundError(HephaestusError):
    """Raised when a requested task ID does not exist."""

    pass


class TaskTimeoutError(HephaestusError):
    """Raised when a task does not complete within the specified timeout."""

    pass


class QdrantConnectionError(HephaestusError):
    """Raised when Qdrant vector store is not accessible."""

    pass


class ProcessSpawnError(HephaestusError):
    """Raised when a process fails to spawn."""

    pass


class RestartError(HephaestusError):
    """Raised when a component fails to restart properly."""

    pass
