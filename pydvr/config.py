"""
Application configuration management.

Uses Pydantic Settings to load configuration from YAML file, environment variables, or .env file.
Configuration priority (highest to lowest):
1. config.yaml (if exists)
2. Environment variables
3. .env file (fallback for backwards compatibility)

Implements the Single Responsibility Principle by centralizing all configuration logic.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from pydvr.paths import get_config_file, get_database_file, get_token_cache_file


def load_yaml_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the YAML configuration file (default: XDG config dir)

    Returns:
        Dict[str, Any]: Configuration dictionary with flattened keys for Pydantic

    Example YAML structure:
        hdhomerun:
          ip: "192.168.1.100"
        schedules_direct:
          username: "user@example.com"

    This gets flattened to:
        {"hdhomerun_ip": "192.168.1.100", "sd_username": "user@example.com"}
    """
    if config_path is None:
        config_path = get_config_file()

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            yaml_data = yaml.safe_load(f) or {}

        # Flatten nested YAML structure to match Pydantic field names
        flattened = {}

        # HDHomeRun settings
        if "hdhomerun" in yaml_data:
            if "ip" in yaml_data["hdhomerun"]:
                flattened["hdhomerun_ip"] = yaml_data["hdhomerun"]["ip"]

        # Schedules Direct settings
        if "schedules_direct" in yaml_data:
            if "username" in yaml_data["schedules_direct"]:
                flattened["sd_username"] = yaml_data["schedules_direct"]["username"]
            if "password" in yaml_data["schedules_direct"]:
                flattened["sd_password"] = yaml_data["schedules_direct"]["password"]

        # Recording settings
        if "recording" in yaml_data:
            if "path" in yaml_data["recording"]:
                flattened["recording_path"] = yaml_data["recording"]["path"]
            if "padding_start" in yaml_data["recording"]:
                flattened["default_padding_start"] = yaml_data["recording"]["padding_start"]
            if "padding_end" in yaml_data["recording"]:
                flattened["default_padding_end"] = yaml_data["recording"]["padding_end"]

        # Database settings
        if "database" in yaml_data:
            if "url" in yaml_data["database"]:
                flattened["database_url"] = yaml_data["database"]["url"]

        # Server settings
        if "server" in yaml_data:
            if "host" in yaml_data["server"]:
                flattened["host"] = yaml_data["server"]["host"]
            if "port" in yaml_data["server"]:
                flattened["port"] = yaml_data["server"]["port"]
            if "debug" in yaml_data["server"]:
                flattened["debug"] = yaml_data["server"]["debug"]
            if "log_level" in yaml_data["server"]:
                flattened["log_level"] = yaml_data["server"]["log_level"]

        # Token cache path
        if "token_cache_path" in yaml_data:
            flattened["token_cache_path"] = yaml_data["token_cache_path"]

        return flattened

    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration file {config_path}: {e}") from e
    except Exception as e:
        raise ValueError(f"Error loading configuration file {config_path}: {e}") from e


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
    hdhomerun_ip: str | None = Field(
        default=None,
        description="IP address of HDHomeRun device on local network",
        examples=["192.168.1.100"],
    )

    # Schedules Direct Configuration
    sd_username: str | None = Field(
        default=None,
        description="Schedules Direct username (email address)",
        examples=["user@example.com"],
    )

    sd_password: str | None = Field(
        default=None,
        description="Schedules Direct password",
        min_length=1,
    )

    # Recording Configuration
    recording_path: Path | None = Field(
        default=None,
        description="Directory where recordings will be saved",
        examples=["/mnt/recordings", "C:/Recordings"],
    )

    # Database Configuration
    database_url: str = Field(
        default_factory=lambda: f"sqlite:///{get_database_file()}",
        description="Database connection URL",
        examples=[
            "sqlite:///~/.local/share/pydvr/pydvr.db",
            "postgresql://user:pass@localhost/pyhdhrdvr",
        ],
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
        default_factory=get_token_cache_file,
        description="Path to Schedules Direct token cache file",
    )

    @field_validator("hdhomerun_ip")
    @classmethod
    def validate_ip_format(cls, v: str | None) -> str | None:
        """
        Validate that HDHomeRun IP is in a reasonable format.

        Note: We do basic format checking but don't verify the device exists
        at this IP - that will be checked at runtime when connecting.
        """
        if v is None:
            return None

        if not v or v.strip() == "":
            raise ValueError("HDHomeRun IP address cannot be empty")

        parts = v.split(".")
        if len(parts) != 4:
            raise ValueError(f"Invalid IP address format: {v}. Expected format: xxx.xxx.xxx.xxx")

        try:
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError(
                        f"Invalid IP address: {v}. Each octet must be between 0 and 255"
                    )
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid IP address: {v}. All parts must be numeric") from e
            raise

        return v

    @field_validator("recording_path")
    @classmethod
    def validate_recording_path(cls, v: Path | None) -> Path | None:
        """
        Validate and prepare the recording path.

        Creates the directory if it doesn't exist and verifies it's writable.
        """
        if v is None:
            return None

        if not v:
            raise ValueError("Recording path cannot be empty")

        # Convert to absolute path
        path = Path(v).resolve()

        # Create directory if it doesn't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise ValueError(f"Cannot create recording directory {path}: Permission denied") from e
        except Exception as e:
            raise ValueError(f"Cannot create recording directory {path}: {e}") from e

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
            raise ValueError(f"Cannot write to recording directory {path}: {e}") from e

        return path

    def is_configured(self) -> bool:
        """
        Check if all required configuration is present.

        Returns:
            bool: True if all required fields are configured, False otherwise
        """
        return all(
            [
                self.hdhomerun_ip is not None,
                self.sd_username is not None,
                self.sd_password is not None,
                self.recording_path is not None,
            ]
        )

    def validate_required(self) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ValueError: If any required configuration is missing
        """
        missing = []
        if self.hdhomerun_ip is None:
            missing.append("hdhomerun_ip")
        if self.sd_username is None:
            missing.append("sd_username")
        if self.sd_password is None:
            missing.append("sd_password")
        if self.recording_path is None:
            missing.append("recording_path")

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                f"Run 'pydvr setup' to configure the application."
            )

    def get_hdhomerun_base_url(self) -> str:
        """Get the base URL for HDHomeRun API calls."""
        if self.hdhomerun_ip is None:
            raise ValueError("HDHomeRun IP not configured. Run 'pydvr setup' first.")
        return f"http://{self.hdhomerun_ip}"

    def get_schedules_direct_base_url(self) -> str:
        """Get the base URL for Schedules Direct API calls."""
        return "https://json.schedulesdirect.org/20141201"


# Global settings instance
# This implements the Singleton pattern for configuration access
_settings: Settings | None = None


def get_settings(config_path: Path | None = None) -> Settings:
    """
    Get or create the global settings instance.

    This function implements lazy loading and provides a single point of access
    to application configuration (Dependency Inversion Principle).

    Configuration is loaded in this priority order:
    1. YAML file (~/.config/pydvr/config.yaml or specified path)
    2. Environment variables
    3. .env file (fallback for backwards compatibility, in current directory)

    Args:
        config_path: Optional path to YAML config file (default: ~/.config/pydvr/config.yaml)

    Returns:
        Settings: The global settings instance

    Example:
        >>> from pydvr.config import get_settings
        >>> settings = get_settings()
        >>> print(settings.hdhomerun_ip)
    """
    global _settings
    if _settings is None:
        # Load YAML config from user config directory
        yaml_config = load_yaml_config(config_path)

        # Create Settings instance
        # Pydantic will merge: YAML values -> env vars -> .env file -> defaults
        if yaml_config:
            _settings = Settings(**yaml_config)
        else:
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
