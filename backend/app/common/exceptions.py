class DomainError(Exception):
    """Base class for business-rule violations that should surface as HTTP 400."""


class NotFoundError(DomainError):
    """Entity not found — surfaces as HTTP 404."""


class ValidationFailedError(DomainError):
    """Business-rule validation failed (e.g. BR-01..BR-10 in the spec)."""

    def __init__(self, message: str, issues: list[str] | None = None):
        super().__init__(message)
        self.issues = issues or [message]
