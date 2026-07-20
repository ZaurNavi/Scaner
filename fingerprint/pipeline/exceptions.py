#!/usr/bin/env python3
"""
Pipeline Exceptions — исключения для Fingerprint Pipeline.
ES-1.8.2: Специализированные исключения для Pipeline.
"""


class FingerprintPipelineError(Exception):
    """Базовое исключение для Fingerprint Pipeline."""
    pass


class BuilderAlreadyBuiltError(FingerprintPipelineError):
    """
    Исключение выбрасывается при попытке использовать Builder после build().
    
    ES-1.8.2:
    После вызова build() Builder автоматически инвалидируется.
    Любой вызов add(), extend(), build() выбрасывает это исключение.
    """
    
    def __init__(self, builder_type: str = "Builder"):
        super().__init__(
            f"{builder_type} has already been built and is invalidated. "
            f"Create a new {builder_type} instance."
        )
        self.builder_type = builder_type


class PipelineExecutionError(FingerprintPipelineError):
    """Исключение выбрасывается при ошибке выполнения Pipeline."""
    
    def __init__(self, stage: str, error: Exception):
        super().__init__(f"Pipeline failed at stage '{stage}': {error}")
        self.stage = stage
        self.original_error = error
