"""
Application configuration management.

Uses Pydantic Settings to load configuration from environment variables and .env file.
Implements the Single Responsibility Principle by centralizing all configuration logic.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    Loads configuration from environment variables and .env file.
    All settings are validated on instantiation.

    Design Principles:
    - Single Responsibility: Handles only configuration management
    - Open/Closed: Can be extended with new settings without modifying existing code
    - Dependency Inversion: Other modules depend on this abstraction, not on env vars directly
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields in .env file
    )

    # HDHomeRun Configuration
    hdhomerun_ip: str = Field(
        ...,
        description="IP address of HDHomeRun device on local network",
        examples=["192.168.1.100"],
    )

    # Schedules Direct Configuration
    sd_username: str = Field(
        ...,
        description="Schedules Direct username (email address)",
        examples=["user@example.com"],
    )

    sd_password: str = Field(
        ...,
        description="Schedules Direct password",
        min_length=1,
    )

    # Recording Configuration
    recording_path: Path = Field(
        ...,
        description="Directory where recordings will be saved",
        examples=["/mnt/recordings", "C:/Recordings"],
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./pyhdhrdvr.db",
        description="Database connection URL",
        examples=["sqlite:///./pyhdhrdvr.db", "postgresql://user:pass@localhost/pyhdhrdvr"],
    )

    # Recording Padding Defaults
    default_padding_start: int = Field(
        default=60,
        description="Default seconds to start recording before scheduled time",
        ge=0,
        le=600,  # Max 10 minutes
    )

    default_padding_end: int = Field(
        default=120,
        description="Default seconds to continue recording after scheduled end time",
        ge=0,
        le=600,  # Max 10 minutes
    )

    # Optional Application Settings
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the application to",
    )

    port: int = Field(
        default=80,
        description="Port to bind the application to",
        ge=1,
        le=65535,
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode with detailed error messages",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    token_cache_path: Path = Field(
        default=Path("./sd_token_cache.json"),
        description="Path to Schedules Direct token cache file",
    )

    @field_validator("hdhomerun_ip")
    @classmethod
    def validate_ip_format(cls, v: str) -> str:
        """
        Validate that HDHomeRun IP is in a reasonable format.

        Note: We do basic format checking but don't verify the device exists
        at this IP - that will be checked at runtime when connecting.
        """
        if not v or v.strip() == "":
            raise ValueError("HDHomeRun IP address cannot be empty")

        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid IP address format: {v}. Expected format: xxx.xxx.xxx.xxx"
            )

        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError(
                        f"Invalid IP address: {v}. Each octet must be between 0 and 255"
                    )
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"Invalid IP address: {v}. All parts must be numeric"
                ) from e
            raise

        return v

    @field_validator("recording_path")
    @classmethod
    def validate_recording_path(cls, v: Path) -> Path:
        """
        Validate and prepare the recording path.

        Creates the directory if it doesn't exist and verifies it's writable.
        """
        if not v:
            raise ValueError("Recording path cannot be empty")

        # Convert to absolute path
        path = Path(v).resolve()

        # Create directory if it doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise ValueError(
                f"Cannot create recording directory {path}: Permission denied"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Cannot create recording directory {path}: {e}"
            ) from e

        # Verify directory is writable
        if not path.is_dir():
            raise ValueError(f"Recording path {path} is not a directory")

        # Test write permissions by trying to create a temp file
        test_file = path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
        except PermissionError as e:
            raise ValueError(
                f"Recording directory {path} is not writable: Permission denied"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Cannot write to recording directory {path}: {e}"
            ) from e

        return path

    def get_hdhomerun_base_url(self) -> str:
        """Get the base URL for HDHomeRun API calls."""
        return f"http://{self.hdhomerun_ip}"

    def get_schedules_direct_base_url(self) -> str:
        """Get the base URL for Schedules Direct API calls."""
        return "https://json.schedulesdirect.org/20141201"


# Global settings instance
# This implements the Singleton pattern for configuration access
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get or create the global settings instance.

    This function implements lazy loading and provides a single point of access
    to application configuration (Dependency Inversion Principle).

    Returns:
        Settings: The global settings instance

    Example:
        >>> from app.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.hdhomerun_ip)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Force reload settings from environment/file.

    Useful for testing or when configuration changes at runtime.

    Returns:
        Settings: The newly loaded settings instance
    """
    global _settings
    _settings = Settings()
    return _settings
