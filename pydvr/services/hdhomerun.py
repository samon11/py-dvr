"""
HDHomeRun device client for tuner control and stream capture.

This module provides HTTP API communication with HDHomeRun network TV tuner devices.
Implements device discovery, tuner status checking, channel tuning, and stream capture.

Design Principles:
- Single Responsibility: Handles only HDHomeRun device communication
- Open/Closed: Can be extended for additional device features
- Dependency Inversion: Uses abstract HTTP client interface (httpx)
"""

import logging
import time
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TunerStatus(str, Enum):
    """Tuner status states from HDHomeRun device."""

    IDLE = "idle"
    IN_USE = "in_use"
    SCANNING = "scanning"
    LOCKED = "locked"
    NO_LOCK = "no_lock"
    ERROR = "error"


class DeviceInfo(BaseModel):
    """HDHomeRun device information from /discover.json."""

    device_id: str = Field(..., description="Unique device identifier (hex)")
    friendly_name: str = Field(..., description="Human-readable device name")
    model_number: str = Field(..., description="Device model (e.g., HDHR5-4K)")
    firmware_name: str = Field(..., description="Firmware version")
    firmware_version: str = Field(..., description="Firmware version string")
    device_auth: str = Field(..., description="Device authentication string")
    tuner_count: int = Field(..., description="Number of available tuners", ge=1)
    base_url: str = Field(..., description="Base HTTP URL for device")
    lineup_url: str = Field(..., description="URL for channel lineup")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "device_id": "12345678",
                "friendly_name": "HDHomeRun PRIME",
                "model_number": "HDHR5-4K",
                "firmware_name": "hdhomerun5_atsc",
                "firmware_version": "20231214",
                "device_auth": "auth_token",
                "tuner_count": 4,
                "base_url": "http://192.168.1.100",
                "lineup_url": "http://192.168.1.100/lineup.json",
            }
        }


class ChannelInfo(BaseModel):
    """Channel information from /lineup.json."""

    guide_number: str = Field(..., description="Channel number (e.g., '2.1')")
    guide_name: str = Field(..., description="Station call sign")
    url: str = Field(..., description="Stream URL for this channel")


class HDHomeRunError(Exception):
    """Base exception for HDHomeRun client errors."""

    pass


class DeviceNotFoundError(HDHomeRunError):
    """Raised when HDHomeRun device cannot be reached."""

    pass


class TunerNotAvailableError(HDHomeRunError):
    """Raised when no tuners are available for recording."""

    pass


class TuningError(HDHomeRunError):
    """Raised when channel tuning fails."""

    pass


class HDHomeRunClient:
    """
    Client for communicating with HDHomeRun network TV tuner devices.

    This client provides methods to:
    - Retrieve device information and capabilities
    - Get channel lineup
    - Stream live TV (tuning happens automatically when streaming starts)
    - Capture MPEG-TS streams to disk

    Important: HDHomeRun combines tuning and streaming in a single operation.
    When you request a stream URL, the device automatically allocates a tuner,
    tunes the channel, and begins streaming. The tuner is released when the
    HTTP connection closes or the duration expires.

    All HTTP communication uses httpx for async/sync flexibility.
    Implements retry logic and proper error handling for network operations.

    Example:
        >>> client = HDHomeRunClient("192.168.1.100")
        >>> device_info = client.get_device_info()
        >>> print(f"Device has {device_info.tuner_count} tuners")
        >>> # Stream directly - tuning happens automatically
        >>> result = client.stream_channel("7.1", "recording.ts", duration=60)
        >>> print(f"Recorded {result['bytes_written']} bytes")
    """

    def __init__(
        self,
        device_ip: str,
        timeout: float = 10.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize HDHomeRun client.

        Args:
            device_ip: IP address of HDHomeRun device
            timeout: HTTP request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.device_ip = device_ip
        self.base_url = f"http://{device_ip}"
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Create HTTP client with reasonable defaults
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

        logger.info(f"Initialized HDHomeRun client for device at {device_ip}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.close()

    def close(self):
        """Close the HTTP client and cleanup resources."""
        if self.client:
            self.client.close()
            logger.debug("Closed HDHomeRun client")

    def _make_request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (relative to base_url)
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            httpx.Response: HTTP response object

        Raises:
            DeviceNotFoundError: If device cannot be reached after retries
            HDHomeRunError: For other HTTP errors
        """
        url = f"{self.base_url}{path}"
        last_error = None

        for attempt in range(self.retry_attempts):
            try:
                logger.debug(
                    f"Request {method} {url} (attempt {attempt + 1}/{self.retry_attempts})"
                )
                response = self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"Request timeout for {url} (attempt {attempt + 1}/{self.retry_attempts})"
                )
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    f"Connection failed to {url} (attempt {attempt + 1}/{self.retry_attempts})"
                )
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                raise HDHomeRunError(
                    f"HTTP {e.response.status_code} error: {e.response.text}"
                ) from e

            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                raise HDHomeRunError(f"Request failed: {e}") from e

        # All retries exhausted
        raise DeviceNotFoundError(
            f"Could not reach HDHomeRun device at {self.device_ip} after "
            f"{self.retry_attempts} attempts: {last_error}"
        )

    def get_device_info(self) -> DeviceInfo:
        """
        Retrieve device information and capabilities.

        Returns:
            DeviceInfo: Device information including model and tuner count

        Raises:
            DeviceNotFoundError: If device cannot be reached
            HDHomeRunError: For other errors

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> info = client.get_device_info()
            >>> print(f"Model: {info.model_number}, Tuners: {info.tuner_count}")
        """
        logger.info(f"Retrieving device info from {self.device_ip}")

        response = self._make_request("GET", "/discover.json")
        data = response.json()

        # Parse device info from response
        device_info = DeviceInfo(
            device_id=data.get("DeviceID", ""),
            friendly_name=data.get("FriendlyName", "HDHomeRun"),
            model_number=data.get("ModelNumber", "Unknown"),
            firmware_name=data.get("FirmwareName", ""),
            firmware_version=data.get("FirmwareVersion", ""),
            device_auth=data.get("DeviceAuth", ""),
            tuner_count=data.get("TunerCount", 1),
            base_url=data.get("BaseURL", self.base_url),
            lineup_url=data.get("LineupURL", f"{self.base_url}/lineup.json"),
        )

        logger.info(
            f"Device info: {device_info.model_number} with {device_info.tuner_count} tuners"
        )
        return device_info

    def get_lineup(self) -> list[ChannelInfo]:
        """
        Retrieve available channels from device lineup.

        Returns:
            list[ChannelInfo]: List of available channels

        Raises:
            DeviceNotFoundError: If device cannot be reached
            HDHomeRunError: For other errors

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> channels = client.get_lineup()
            >>> for channel in channels:
            ...     print(f"{channel.guide_number}: {channel.guide_name}")
        """
        logger.info(f"Retrieving channel lineup from {self.device_ip}")

        response = self._make_request("GET", "/lineup.json")
        data = response.json()

        channels = [
            ChannelInfo(
                guide_number=channel.get("GuideNumber", ""),
                guide_name=channel.get("GuideName", ""),
                url=channel.get("URL", ""),
            )
            for channel in data
        ]

        logger.info(f"Retrieved {len(channels)} channels from lineup")
        return channels

    def find_available_tuner(self) -> int:
        """
        Find the first available tuner by attempting to tune with 'auto'.

        Note: HDHomeRun API doesn't provide a direct way to check tuner status.
        We rely on the 'auto' tuner selection which automatically picks an available tuner.
        This method simply returns 0 as a placeholder - actual tuner selection
        happens when you use tuner_id='auto' in tune_channel() or stream_channel().

        Returns:
            int: Always returns 0 (use tuner_id='auto' for actual tuner selection)

        Raises:
            DeviceNotFoundError: If device cannot be reached

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> # Don't use this tuner number directly, use 'auto' instead
            >>> result = client.stream_channel("7.1", output_path="test.ts",
            ...                                duration=10, tuner_id="auto")
        """
        logger.info("Note: HDHomeRun uses 'auto' for tuner selection")

        # Verify device is reachable
        self.get_device_info()

        # Return 0 as placeholder - caller should use 'auto' for tuner_id
        logger.info("Use tuner_id='auto' for automatic tuner selection")
        return 0

    def verify_channel(self, channel: str) -> bool:
        """
        Verify that a channel exists in the device lineup.

        This is a helper method to check channel validity before attempting to stream.
        Note: This is optional - streaming will return 404 if channel doesn't exist.

        Args:
            channel: Channel number (e.g., "2.1", "7.1")

        Returns:
            bool: True if channel exists in lineup, False otherwise

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> if client.verify_channel("7.1"):
            ...     print("Channel 7.1 is available")
        """
        try:
            lineup = self.get_lineup()
            return any(ch.guide_number == channel for ch in lineup)
        except Exception as e:
            logger.warning(f"Could not verify channel {channel}: {e}")
            return False

    def get_stream_url(
        self,
        channel: str,
        tuner_id: str = "auto",
        duration: int | None = None,
    ) -> str:
        """
        Build the URL for streaming MPEG-TS data from a channel.

        Args:
            channel: Channel number (e.g., "2.1", "7.1")
            tuner_id: Tuner identifier ('auto', 'tuner0', 'tuner1', etc.)
                     'auto' lets the device select an available tuner
            duration: Optional duration limit in seconds

        Returns:
            str: URL for MPEG-TS stream

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> url = client.get_stream_url("7.1", tuner_id="auto", duration=300)
            >>> # http://192.168.1.100:5004/auto/v7.1?duration=300
        """
        # Use port 5004 for streaming as per HDHomeRun API spec
        base = f"http://{self.device_ip}:5004"
        url = f"{base}/{tuner_id}/v{channel}"

        if duration is not None:
            url += f"?duration={duration}"

        logger.debug(f"Stream URL: {url}")
        return url

    def release_tuner(self, tuner_id: str) -> None:
        """
        Release a tuner by setting its channel to 'none'.

        Note: Tuners are automatically released when the HTTP streaming connection
        closes, so this method is typically not needed. It's provided for cases
        where you want to explicitly release a tuner without waiting for connection
        cleanup.

        Args:
            tuner_id: Tuner identifier ('tuner0', 'tuner1', etc.)
                     Note: Cannot use 'auto' for release - must specify exact tuner

        Raises:
            HDHomeRunError: If release fails
            ValueError: If tuner_id is 'auto'

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> client.release_tuner("tuner0")
            >>> # Tuner 0 is now available for other uses
        """
        if tuner_id == "auto":
            raise ValueError("Cannot release 'auto' tuner - must specify exact tuner ID")

        logger.info(f"Releasing {tuner_id}")

        # Note: Release happens on port 5004
        release_url = f"http://{self.device_ip}:5004/{tuner_id}/vnone"
        try:
            logger.debug(f"Releasing via: {release_url}")
            response = self.client.request("GET", release_url)
            response.raise_for_status()
            logger.debug(f"Release response: {response.text}")
            logger.info(f"{tuner_id} released successfully")
        except Exception as e:
            logger.error(f"Failed to release {tuner_id}: {e}")
            raise HDHomeRunError(f"Failed to release {tuner_id}: {e}") from e

    def stream_channel(
        self,
        channel: str,
        output_path: Path | str,
        duration: int,
        tuner_id: str = "auto",
        chunk_size: int = 1024 * 1024,  # 1 MB chunks
        max_resume_attempts: int = 3,
        resume_delay: float = 2.0,
    ) -> dict[str, Any]:
        """
        Capture a live TV stream to a file with automatic resumption on errors.

        This method handles the complete workflow:
        1. Tune to the channel
        2. Stream MPEG-TS data to file
        3. Monitor for errors and resume streaming if interrupted
        4. Release the tuner when done

        Args:
            channel: Channel number (e.g., "2.1", "7.1")
            output_path: Path where recording file will be saved
            duration: Recording duration in seconds
            tuner_id: Tuner identifier ('auto', 'tuner0', 'tuner1', etc.)
            chunk_size: Size of chunks to read/write (default: 1 MB)
            max_resume_attempts: Maximum number of times to resume after errors
            resume_delay: Seconds to wait before resuming after an error

        Returns:
            dict with recording metadata:
                - tuner_id: The tuner that was used
                - bytes_written: Total bytes written to file
                - duration: Actual recording duration
                - success: Whether recording completed successfully
                - resume_count: Number of times stream was resumed

        Raises:
            TuningError: If channel tuning fails
            TunerNotAvailableError: If no tuner is available
            HDHomeRunError: For other streaming errors after all resume attempts

        Example:
            >>> client = HDHomeRunClient("192.168.1.100")
            >>> result = client.stream_channel(
            ...     channel="7.1",
            ...     output_path="/recordings/test.ts",
            ...     duration=300,  # 5 minutes
            ...     tuner_id="auto"
            ... )
            >>> print(f"Recorded {result['bytes_written']} bytes")
        """
        output_path = Path(output_path)
        logger.info(
            f"Starting stream capture: channel={channel}, duration={duration}s, "
            f"output={output_path}, tuner={tuner_id}"
        )

        # Track which tuner we're using
        actual_tuner_id = tuner_id
        bytes_written = 0
        start_time = time.time()
        resume_count = 0
        write_mode = "wb"  # First write is binary write mode

        try:
            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Note: Tuning happens automatically when we start streaming.
            # The HDHomeRun API combines tuning and streaming in a single operation.

            # Attempt streaming with resume capability
            while resume_count <= max_resume_attempts:
                try:
                    # Calculate remaining time for this attempt
                    elapsed = time.time() - start_time
                    remaining_duration = duration - int(elapsed)

                    if remaining_duration <= 0:
                        logger.info("Recording duration reached")
                        break

                    # Build stream URL with remaining duration
                    stream_url = self.get_stream_url(
                        channel=channel,
                        tuner_id=actual_tuner_id,
                        duration=remaining_duration,
                    )

                    # Stream to file
                    action = "Resuming" if resume_count > 0 else "Starting"
                    attempt = f"{resume_count + 1}/{max_resume_attempts + 1}"
                    logger.info(
                        f"{action} stream from {stream_url} (attempt {attempt})"
                    )

                    # Use the client's stream method with infinite timeout for streaming
                    with self.client.stream(
                        "GET", stream_url, timeout=httpx.Timeout(None)
                    ) as response:
                        response.raise_for_status()

                        with open(output_path, write_mode) as f:
                            for chunk in response.iter_bytes(chunk_size=chunk_size):
                                if chunk:
                                    f.write(chunk)
                                    bytes_written += len(chunk)

                                # Check if we've exceeded duration (safety check)
                                elapsed = time.time() - start_time
                                if elapsed > duration + 10:  # 10 second grace period
                                    logger.info(
                                        f"Recording duration reached "
                                        f"({elapsed:.1f}s >= {duration}s)"
                                    )
                                    # Break out of chunk iteration
                                    break

                    # If we get here, streaming completed successfully
                    break

                except StopIteration:
                    # Normal completion - duration reached
                    break

                except (httpx.ReadError, httpx.RemoteProtocolError, httpx.ReadTimeout) as e:
                    # Network/stream errors that we can recover from
                    resume_count += 1

                    if resume_count > max_resume_attempts:
                        logger.error(
                            f"Stream interrupted and max resume attempts "
                            f"({max_resume_attempts}) exceeded: {e}"
                        )
                        raise HDHomeRunError(
                            f"Stream failed after {resume_count} resume attempts: {e}"
                        ) from e

                    error_name = type(e).__name__
                    attempt_info = f"{resume_count}/{max_resume_attempts}"
                    logger.warning(
                        f"Stream interrupted ({error_name}: {e}), "
                        f"resuming in {resume_delay}s (attempt {attempt_info})"
                    )

                    # Switch to append mode for resume attempts
                    write_mode = "ab"

                    # Wait before resuming
                    time.sleep(resume_delay)

                    # Note: We cannot verify tuner status via API
                    # Simply attempt to resume the stream
                    # If the tuner lost signal, the stream request will fail with 503
                    logger.debug("Attempting to resume stream...")

                    # Continue to next iteration to resume streaming

                except httpx.HTTPStatusError as e:
                    # HTTP errors - don't retry these
                    logger.error(f"HTTP error during stream capture: {e}")
                    if e.response.status_code == 503:
                        raise TunerNotAvailableError(
                            f"Stream unavailable for channel {channel}: {e}"
                        ) from e
                    elif e.response.status_code == 404:
                        raise TuningError(f"Unknown channel {channel}: {e}") from e
                    else:
                        raise HDHomeRunError(f"Stream error: {e}") from e

            elapsed_time = time.time() - start_time
            logger.info(
                f"Stream capture completed: {bytes_written:,} bytes in {elapsed_time:.1f}s "
                f"({bytes_written / elapsed_time / 1024 / 1024:.2f} MB/s)"
                + (f", {resume_count} resume(s)" if resume_count > 0 else "")
            )

            return {
                "tuner_id": actual_tuner_id,
                "bytes_written": bytes_written,
                "duration": elapsed_time,
                "success": True,
                "resume_count": resume_count,
            }

        except (TuningError, TunerNotAvailableError):
            # Re-raise tuning-related errors
            raise

        except Exception as e:
            logger.error(f"Error during stream capture: {e}")
            raise HDHomeRunError(f"Stream capture failed: {e}") from e

        finally:
            # Note: Tuners are automatically released when the HTTP connection closes.
            # The streaming context manager handles this, so explicit release is not needed.
            # We only need to ensure the httpx client is closed properly (handled by __exit__).
            logger.debug(
                f"Stream capture finished. Tuner {actual_tuner_id} will be "
                f"released automatically when connection closes."
            )

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"HDHomeRunClient(device_ip='{self.device_ip}')"
