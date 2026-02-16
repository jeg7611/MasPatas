class DomainError(Exception):
    """Base para errores de dominio."""


class BusinessRuleViolation(DomainError):
    """Violación explícita de regla de negocio."""


class InsufficientStockError(BusinessRuleViolation):
    """Se lanza cuando no hay inventario suficiente para vender."""


class UnauthorizedOperationError(DomainError):
    """Operación no permitida por reglas de seguridad."""
