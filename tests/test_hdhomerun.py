"""
Tests for HDHomeRun client.

These tests require a real HDHomeRun device on the network.
Set HDHOMERUN_IP environment variable or update the test configuration.

NO MOCKING - All tests run against a real device to verify actual behavior.
"""

import os
import time
from pathlib import Path

import pytest

from pydvr.services.hdhomerun import (
    ChannelInfo,
    DeviceInfo,
    DeviceNotFoundError,
    HDHomeRunClient,
    TunerNotAvailableError,
    TuningError,
)


# Test configuration - update with your device IP
TEST_DEVICE_IP = os.getenv("HDHOMERUN_IP", "192.168.1.177")
TEST_CHANNEL = os.getenv("TEST_CHANNEL", "7.1")  # Update with a valid channel


class TestHDHomeRunClient:
    """Tests for HDHomeRunClient with real device."""

    @pytest.fixture
    def client(self):
        """Create client for tests."""
        client = HDHomeRunClient(TEST_DEVICE_IP, timeout=5.0)
        yield client
        client.close()

    def test_init(self, client):
        """Test client initialization."""
        assert client.device_ip == TEST_DEVICE_IP
        assert client.base_url == f"http://{TEST_DEVICE_IP}"
        assert client.timeout == 5.0

    def test_context_manager(self):
        """Test client as context manager."""
        with HDHomeRunClient(TEST_DEVICE_IP) as client:
            assert client.client is not None
        # Client should be closed after context exit

    def test_get_device_info(self, client):
        """Test retrieving device information."""
        try:
            info = client.get_device_info()
            assert isinstance(info, DeviceInfo)
            assert info.device_id
            assert info.model_number
            assert info.tuner_count > 0
            print(f"\nDevice: {info.model_number} with {info.tuner_count} tuners")
        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")

    def test_get_lineup(self, client):
        """Test retrieving channel lineup."""
        try:
            channels = client.get_lineup()
            assert isinstance(channels, list)
            assert len(channels) > 0
            assert all(isinstance(ch, ChannelInfo) for ch in channels)
            assert all(ch.guide_number for ch in channels)
            assert all(ch.guide_name for ch in channels)
            print(f"\nFound {len(channels)} channels")
            if channels[:3]:
                for ch in channels[:3]:
                    print(f"  {ch.guide_number}: {ch.guide_name}")
        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")

    def test_find_available_tuner(self, client):
        """Test finding an available tuner."""
        try:
            tuner_num = client.find_available_tuner()
            assert isinstance(tuner_num, int)
            assert tuner_num >= 0
            print(f"\nFound available tuner: {tuner_num}")
        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")
        except TunerNotAvailableError:
            pytest.skip("No tuners available (all in use)")

    def test_get_stream_url(self, client):
        """Test building stream URL."""
        # Test with auto tuner
        url = client.get_stream_url("7.1", tuner_id="auto")
        assert url == f"http://{TEST_DEVICE_IP}:5004/auto/v7.1"

        # Test with specific tuner
        url = client.get_stream_url("7.1", tuner_id="tuner0")
        assert url == f"http://{TEST_DEVICE_IP}:5004/tuner0/v7.1"

        # Test with duration
        url = client.get_stream_url("7.1", tuner_id="auto", duration=300)
        assert url == f"http://{TEST_DEVICE_IP}:5004/auto/v7.1?duration=300"

    def test_repr(self, client):
        """Test string representation."""
        repr_str = repr(client)
        assert "HDHomeRunClient" in repr_str
        assert TEST_DEVICE_IP in repr_str


class TestHDHomeRunTuning:
    """Tests for channel tuning functionality."""

    @pytest.fixture
    def client(self):
        """Create client for tests."""
        client = HDHomeRunClient(TEST_DEVICE_IP, timeout=10.0)
        yield client
        client.close()

    def test_release_tuner_validation(self, client):
        """Test that releasing 'auto' tuner raises error."""
        with pytest.raises(ValueError, match="Cannot release 'auto'"):
            client.release_tuner("auto")


class TestHDHomeRunStreaming:
    """Tests for stream capture functionality."""

    @pytest.fixture
    def client(self):
        """Create client for tests."""
        client = HDHomeRunClient(TEST_DEVICE_IP, timeout=10.0)
        yield client
        client.close()

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create temporary directory for recordings."""
        output_dir = tmp_path / "recordings"
        output_dir.mkdir()
        return output_dir

    @pytest.mark.slow
    def test_stream_channel_short_recording(self, client, temp_output_dir):
        """Test capturing a short stream (10 seconds)."""
        output_file = temp_output_dir / "test_recording.ts"

        try:
            result = client.stream_channel(
                channel=TEST_CHANNEL,
                output_path=output_file,
                duration=10,  # 10 seconds
                tuner_id="auto",
            )

            # Verify result
            assert result["success"] is True
            assert result["bytes_written"] > 0
            assert result["duration"] >= 10
            assert result["tuner_id"] in ["auto", "tuner0", "tuner1", "tuner2", "tuner3"]
            assert "resume_count" in result

            # Verify file was created
            assert output_file.exists()
            assert output_file.stat().st_size > 0
            assert output_file.stat().st_size == result["bytes_written"]

            print(f"\nRecorded {result['bytes_written']:,} bytes in {result['duration']:.1f}s")
            print(f"File size: {output_file.stat().st_size:,} bytes")
            print(f"Resume count: {result['resume_count']}")

        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")
        except TunerNotAvailableError:
            pytest.skip("No tuners available")
        except TuningError as e:
            pytest.skip(f"Could not tune channel {TEST_CHANNEL}: {e}")

    @pytest.mark.slow
    def test_stream_channel_with_specific_tuner(self, client, temp_output_dir):
        """Test stream capture with a specific tuner."""
        output_file = temp_output_dir / "test_specific_tuner.ts"

        try:
            # Use tuner0 for testing
            tuner_id = "tuner0"

            result = client.stream_channel(
                channel=TEST_CHANNEL,
                output_path=output_file,
                duration=5,  # 5 seconds
                tuner_id=tuner_id,
            )

            # Verify result
            assert result["success"] is True
            assert result["bytes_written"] > 0
            assert result["tuner_id"] == tuner_id

            # Verify file exists
            assert output_file.exists()

            print(f"\nRecorded using {tuner_id}: {result['bytes_written']:,} bytes")

        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")
        except TunerNotAvailableError:
            pytest.skip("No tuners available")
        except TuningError as e:
            pytest.skip(f"Could not tune channel {TEST_CHANNEL}: {e}")

    @pytest.mark.slow
    def test_stream_resumption_parameters(self, client, temp_output_dir):
        """Test stream capture with custom resumption parameters."""
        output_file = temp_output_dir / "test_resume_params.ts"

        try:
            result = client.stream_channel(
                channel=TEST_CHANNEL,
                output_path=output_file,
                duration=5,
                tuner_id="auto",
                max_resume_attempts=5,
                resume_delay=1.0,
            )

            # Verify result
            assert result["success"] is True
            assert "resume_count" in result
            assert output_file.exists()

            print(f"\nRecorded with custom resume params: {result['bytes_written']:,} bytes")
            print(f"Resume attempts used: {result['resume_count']}")

        except DeviceNotFoundError:
            pytest.skip(f"HDHomeRun device not found at {TEST_DEVICE_IP}")
        except TunerNotAvailableError:
            pytest.skip("No tuners available")
        except TuningError as e:
            pytest.skip(f"Could not tune channel {TEST_CHANNEL}: {e}")


def test_connection_with_invalid_ip():
    """Test that connecting to invalid IP raises appropriate error."""
    client = HDHomeRunClient("192.168.99.99", retry_attempts=1, retry_delay=0.1, timeout=1.0)

    with pytest.raises(DeviceNotFoundError) as exc_info:
        client.get_device_info()

    assert "Could not reach HDHomeRun device" in str(exc_info.value)
    client.close()


def test_manual_connection():
    """
    Manual test function for quick verification.

    Run this directly to test basic connectivity:
        pytest tests/test_hdhomerun.py::test_manual_connection -s
    """
    print(f"\n{'='*60}")
    print(f"Testing connection to HDHomeRun at {TEST_DEVICE_IP}")
    print(f"{'='*60}\n")

    try:
        with HDHomeRunClient(TEST_DEVICE_IP) as client:
            # Test device info
            print("1. Getting device info...")
            info = client.get_device_info()
            print(f"   [OK] Device: {info.model_number}")
            print(f"   [OK] Tuners: {info.tuner_count}")
            print(f"   [OK] Firmware: {info.firmware_version}\n")

            # Test lineup
            print("2. Getting channel lineup...")
            channels = client.get_lineup()
            print(f"   [OK] Found {len(channels)} channels")
            if channels[:3]:
                for ch in channels[:3]:
                    print(f"     - {ch.guide_number}: {ch.guide_name}")
            print()

            # Note about tuner status
            print("3. Note about tuner status...")
            print(f"   Device has {info.tuner_count} tuners")
            print("   Note: HDHomeRun API doesn't provide direct tuner status queries")
            print("   Use tuner_id='auto' for automatic tuner selection")
            print()

            # Test stream URL generation
            print("4. Testing stream URL generation...")
            stream_url = client.get_stream_url(TEST_CHANNEL, tuner_id="auto", duration=60)
            print(f"   [OK] Stream URL: {stream_url}")
            print(f"   [OK] Test channel: {TEST_CHANNEL}\n")

            print("="*60)
            print("All tests passed! HDHomeRun client is working correctly.")
            print("="*60)

    except DeviceNotFoundError as e:
        print(f"ERROR: {e}")
        print("\nTroubleshooting:")
        print(f"1. Verify HDHomeRun device is online at {TEST_DEVICE_IP}")
        print(f"2. Try: curl http://{TEST_DEVICE_IP}/discover.json")
        print("3. Check firewall settings")
        pytest.fail(str(e))

    except Exception as e:
        print(f"ERROR: {e}")
        pytest.fail(str(e))


if __name__ == "__main__":
    # Run manual test when executed directly
    test_manual_connection()
