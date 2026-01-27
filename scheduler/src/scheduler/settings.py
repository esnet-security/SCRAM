"""Application settings loaded from environment variables."""

from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """SCRAM Scheduler settings."""

    celery_broker_url: str
    celery_result_backend: str
    scram_api_url: str

    process_updates_timeout_interval: int = 1  # seconds
    process_updates_interval: int = 30  # seconds
    disable_process_updates: bool = False  # Can be used for debugging multi-scram stuff

    @model_validator(mode="after")
    def _validate_intervals(self) -> Self:
        if self.process_updates_interval <= self.process_updates_timeout_interval:
            err_msg = (
                f"process_updates_interval ({self.process_updates_interval}) "
                f"must be greater than process_updates_timeout_interval "
                f"({self.process_updates_timeout_interval})"
            )
            raise ValueError(err_msg)

        return self


settings = Settings()  # type: ignore[call-arg]
