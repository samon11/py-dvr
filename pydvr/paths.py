"""
Application paths management.

Provides consistent, platform-independent paths for configuration, logs, and data
using XDG Base Directory specification (Linux/Mac) and AppData (Windows).

This ensures PyDVR can be run from any directory and will always find its
configuration and data files.
"""

import os
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """
    Get the application data directory.

    Uses platform-specific conventions:
    - Linux/Mac: $XDG_DATA_HOME/pydvr or ~/.local/share/pydvr
    - Windows: %APPDATA%/PyDVR

    Returns:
        Path: Application data directory (created if it doesn't exist)

    Example:
        >>> data_dir = get_app_data_dir()
        >>> print(data_dir)
        /home/user/.local/share/pydvr
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        app_dir = base / "PyDVR"
    else:  # Linux/Mac
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        app_dir = base / "pydvr"

    # Create directory if it doesn't exist
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_config_dir() -> Path:
    """
    Get the configuration directory.

    Uses platform-specific conventions:
    - Linux/Mac: $XDG_CONFIG_HOME/pydvr or ~/.config/pydvr
    - Windows: %APPDATA%/PyDVR

    Returns:
        Path: Configuration directory (created if it doesn't exist)

    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)
        /home/user/.config/pydvr
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        config_dir = base / "PyDVR"
    else:  # Linux/Mac
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        config_dir = base / "pydvr"

    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_log_dir() -> Path:
    """
    Get the log directory.

    Uses platform-specific conventions:
    - Linux/Mac: $XDG_STATE_HOME/pydvr or ~/.local/state/pydvr
    - Windows: %LOCALAPPDATA%/PyDVR/logs

    Returns:
        Path: Log directory (created if it doesn't exist)

    Example:
        >>> log_dir = get_log_dir()
        >>> print(log_dir)
        /home/user/.local/state/pydvr
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        log_dir = base / "PyDVR" / "logs"
    else:  # Linux/Mac
        base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
        log_dir = base / "pydvr"

    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_cache_dir() -> Path:
    """
    Get the cache directory.

    Uses platform-specific conventions:
    - Linux/Mac: $XDG_CACHE_HOME/pydvr or ~/.cache/pydvr
    - Windows: %LOCALAPPDATA%/PyDVR/cache

    Returns:
        Path: Cache directory (created if it doesn't exist)

    Example:
        >>> cache_dir = get_cache_dir()
        >>> print(cache_dir)
        /home/user/.cache/pydvr
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        cache_dir = base / "PyDVR" / "cache"
    else:  # Linux/Mac
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        cache_dir = base / "pydvr"

    # Create directory if it doesn't exist
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_config_file(filename: str = "config.yaml") -> Path:
    """
    Get the path to a configuration file.

    Args:
        filename: Name of the config file (default: config.yaml)

    Returns:
        Path: Full path to the configuration file

    Example:
        >>> config_file = get_config_file()
        >>> print(config_file)
        /home/user/.config/pydvr/config.yaml
    """
    return get_config_dir() / filename


def get_log_file(filename: str = "pydvr.log") -> Path:
    """
    Get the path to a log file.

    Args:
        filename: Name of the log file (default: pydvr.log)

    Returns:
        Path: Full path to the log file

    Example:
        >>> log_file = get_log_file()
        >>> print(log_file)
        /home/user/.local/state/pydvr/pydvr.log
    """
    return get_log_dir() / filename


def get_database_file(filename: str = "pydvr.db") -> Path:
    """
    Get the path to the database file.

    Args:
        filename: Name of the database file (default: pydvr.db)

    Returns:
        Path: Full path to the database file

    Example:
        >>> db_file = get_database_file()
        >>> print(db_file)
        /home/user/.local/share/pydvr/pydvr.db
    """
    return get_app_data_dir() / filename


def get_token_cache_file(filename: str = "sd_token_cache.json") -> Path:
    """
    Get the path to the token cache file.

    Args:
        filename: Name of the token cache file (default: sd_token_cache.json)

    Returns:
        Path: Full path to the token cache file

    Example:
        >>> token_file = get_token_cache_file()
        >>> print(token_file)
        /home/user/.cache/pydvr/sd_token_cache.json
    """
    return get_cache_dir() / filename


def print_paths():
    """
    Print all PyDVR paths for debugging and user information.

    This is useful for troubleshooting and showing users where files are stored.
    """
    print("PyDVR Directory Locations:")
    print(f"  Config dir:  {get_config_dir()}")
    print(f"  Data dir:    {get_app_data_dir()}")
    print(f"  Log dir:     {get_log_dir()}")
    print(f"  Cache dir:   {get_cache_dir()}")
    print()
    print("PyDVR File Locations:")
    print(f"  Config file: {get_config_file()}")
    print(f"  Database:    {get_database_file()}")
    print(f"  Log file:    {get_log_file()}")
    print(f"  Token cache: {get_token_cache_file()}")
