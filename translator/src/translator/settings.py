"""Application settings loaded from environment variables."""

from enum import StrEnum
from typing import Annotated

from pydantic import AnyWebsocketUrl, computed_field, field_validator
from pydantic.fields import Field
from pydantic_settings import BaseSettings

TCPUDPPort = Annotated[int, Field(ge=1, le=65535)]


class DebuggerTypes(StrEnum):
    """Supported debuggers."""

    PYCHARM_PYDEVD = "pycharm-pydevd"
    DEBUGPY = "debugpy"


class Settings(BaseSettings):
    """SCRAM Translator settings."""

    log_level: str = "INFO"
    debug: DebuggerTypes | None = None

    # GoBGP Connection Specifics
    gobgp_host: str = "gobgp"
    gobgp_port: TCPUDPPort = 50051

    @computed_field
    @property
    def gobgp_url(self) -> str:
        """Return the composed GoBGP gRPC URL."""
        return f"{self.gobgp_host}:{self.gobgp_port}"

    # SCRAM Connection Specifics
    scram_hostname: str = "scram_hostname_not_set"
    scram_events_url: str = "ws://django:8000/ws/route_manager/translator_block/"

    # GoBGP ASpath defaults (fallback values when event_data doesn't provide them)
    default_asn: int = 65400
    default_community: int = 666
    default_v4_nexthop: str = "192.0.2.199"
    default_v6_nexthop: str = "100::1"

    # Custom Validator(s)
    @field_validator("scram_events_url")
    @classmethod
    def _validate_scram_events_url(cls, v: str) -> str:
        """Validate that the url is a valid WebSocket URL *and* has a trailing slash.

        Returns:
            str: The validated WebSocket URL with a trailing slash.

        Raises:
            ValueError: If the URL is not a valid WebSocket URL or does not have a trailing slash.
        """
        # check to make sure that this is actually a valid websocket URL
        parsed_url = AnyWebsocketUrl(v)
        # then make sure that the trailing slash is actually there.
        if not (parsed_url.path and parsed_url.path.endswith("/")):
            msg = f"scram_events_url: {v!r} must have a trailing slash"
            raise ValueError(msg)
        return v


settings = Settings()  # type: ignore[call-arg]
