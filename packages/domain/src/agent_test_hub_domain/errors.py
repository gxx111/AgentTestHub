from __future__ import annotations


class DomainError(Exception):
    """领域层根异常"""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(DomainError):
    """资源不存在 (404 语义)"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} with ID '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class TenantAccessDeniedError(DomainError):
    """租户越权隔离保护 (多租户安全拦截)"""

    def __init__(self, workspace_id: str, resource_id: str):
        super().__init__(
            f"Access denied: resource '{resource_id}' does not belong to workspace '{workspace_id}'.",
            code="TENANT_ACCESS_DENIED",
        )
        self.workspace_id = workspace_id
        self.resource_id = resource_id


class ValidationError(DomainError):
    """业务参数或契约校验异常"""

    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION_ERROR")


class ConcurrencyConflictError(DomainError):
    """并发写冲突或状态已变更"""

    def __init__(self, message: str):
        super().__init__(message, code="CONCURRENCY_CONFLICT")


class ExperimentCancelledError(DomainError):
    """实验被人工中断取消"""

    def __init__(self, experiment_id: str):
        super().__init__(
            f"Experiment '{experiment_id}' has been cancelled by user.",
            code="EXPERIMENT_CANCELLED",
        )
        self.experiment_id = experiment_id
