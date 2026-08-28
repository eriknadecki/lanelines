class ServiceError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class InviteInvalidError(ServiceError):
    pass


class UserAlreadyExistsError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class InsufficientFundsError(ServiceError):
    pass


class MarketNotTradableError(ServiceError):
    pass


class NotFoundError(ServiceError):
    pass


class AlreadyResolvedError(ServiceError):
    pass


class AlreadyExistsError(ServiceError):
    """Raised when a name/identifier that must be unique is already taken."""


class DeletionBlockedError(ServiceError):
    """Raised when deleting something would orphan real activity (trades,
    payouts) or another record that still references it."""
