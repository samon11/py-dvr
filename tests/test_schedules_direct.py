import json
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio

from pydvr.config import get_settings
from pydvr.schemas.schedules_direct import (
    LineupStationsResponse,
    ProgramsResponse,
    ScheduleMD5Response,
    SchedulesResponse,
    TokenResponse,
    UserLineup,
)
from pydvr.services.schedules_direct import SchedulesDirectClient, SDError

# IMPORTANT: These tests require real Schedules Direct credentials.


@pytest_asyncio.fixture(scope="function")
async def sd_client(tmp_path_factory):
    """
    Pytest fixture for SchedulesDirectClient.
    Initializes the client with real settings and a temporary token cache path.
    """
    settings = get_settings()
    if not settings.sd_username or not settings.sd_password:
        pytest.skip("Schedules Direct credentials (SD_USERNAME, SD_PASSWORD) not set.")

    # Create a temporary directory for the token cache for this test module
    temp_cache_dir = tmp_path_factory.mktemp("sd_cache")
    temp_cache_path = temp_cache_dir / "sd_token_cache.json"

    # Override the token_cache_path in settings for the test
    original_token_cache_path = settings.token_cache_path
    settings.token_cache_path = temp_cache_path

    client = SchedulesDirectClient()
    yield client
    await client.client.aclose()  # Close the httpx.AsyncClient
    settings.token_cache_path = original_token_cache_path  # Restore original path


class TestSchedulesDirectClientIntegration:
    """
    Comprehensive integration tests for SchedulesDirectClient.
    These tests make real API calls to the Schedules Direct service.
    NO MOCKING IS ALLOWED for httpx.AsyncClient or app.config.get_settings.
    """

    # --- Token Management Tests ---

    @pytest.mark.asyncio
    async def test_get_cached_token_no_cache_file(self, sd_client):
        """Test _get_cached_token when no cache file exists."""
        sd_client._token = None
        sd_client._token_expires = None
        sd_client.settings.token_cache_path.unlink(missing_ok=True)  # Ensure no file
        cached_token = await sd_client._get_cached_token()
        assert cached_token is None

    @pytest.mark.asyncio
    async def test_get_cached_token_expired_token(self, sd_client):
        """Test _get_cached_token with an expired token."""
        sd_client._token = None
        sd_client._token_expires = None
        expired_timestamp = int((datetime.now(UTC) - timedelta(days=1)).timestamp())
        with open(sd_client.settings.token_cache_path, "w") as f:
            json.dump({"token": "expired_token", "tokenExpires": expired_timestamp}, f)

        cached_token = await sd_client._get_cached_token()
        assert cached_token is None

    @pytest.mark.asyncio
    async def test_get_cached_token_valid_token(self, sd_client):
        """Test _get_cached_token with a valid token."""
        sd_client._token = None
        sd_client._token_expires = None
        valid_timestamp = int((datetime.now(UTC) + timedelta(days=1)).timestamp())
        expected_token = "valid_test_token"
        with open(sd_client.settings.token_cache_path, "w") as f:
            json.dump({"token": expected_token, "tokenExpires": valid_timestamp}, f)

        cached_token = await sd_client._get_cached_token()
        assert cached_token == (expected_token, valid_timestamp)

    @pytest.mark.asyncio
    async def test_save_token(self, sd_client):
        """Test _save_token to ensure the token is correctly written."""
        test_token = "new_test_token_123"
        test_expires = int((datetime.now(UTC) + timedelta(hours=1)).timestamp())
        await sd_client._save_token(test_token, test_expires)

        with open(sd_client.settings.token_cache_path) as f:
            data = json.load(f)
        assert data["token"] == test_token
        assert data["tokenExpires"] == test_expires

    @pytest.mark.asyncio
    async def test_authenticate_successful(self, sd_client):
        """Test authenticate for successful authentication."""
        sd_client._token = None
        sd_client._token_expires = None
        sd_client.settings.token_cache_path.unlink(missing_ok=True)  # Ensure no cache

        token_response = await sd_client.authenticate()

        assert isinstance(token_response, TokenResponse)
        assert token_response.code == 0
        assert token_response.token is not None
        assert token_response.tokenExpires > datetime.now(UTC).timestamp()
        assert sd_client._token == token_response.token
        assert sd_client._token_expires == token_response.tokenExpires

        # Verify token is cached
        with open(sd_client.settings.token_cache_path) as f:
            cached_data = json.load(f)
        assert cached_data["token"] == token_response.token
        assert cached_data["tokenExpires"] == token_response.tokenExpires

    @pytest.mark.asyncio
    async def test_authenticate_uses_valid_cached_token(self, sd_client):
        """Test authenticate when a valid token is already present in cache."""
        # Manually set a valid token in cache and in client's internal state
        expected_token = "pre_existing_valid_token"
        expected_expires = int((datetime.now(UTC) + timedelta(days=2)).timestamp())
        with open(sd_client.settings.token_cache_path, "w") as f:
            json.dump({"token": expected_token, "tokenExpires": expected_expires}, f)
        sd_client._token = expected_token
        sd_client._token_expires = expected_expires

        # Call authenticate, it should use the cached token
        token_response = await sd_client.authenticate()

        assert isinstance(token_response, TokenResponse)
        assert token_response.token == expected_token
        assert token_response.tokenExpires == expected_expires
        assert token_response.serverID == "cached"  # Should indicate it came from cache
        assert sd_client._token == expected_token
        assert sd_client._token_expires == expected_expires

    @pytest.mark.asyncio
    async def test_ensure_token_triggers_authenticate_no_token(self, sd_client):
        """Test _ensure_token triggers authenticate when no token is present."""
        sd_client._token = None
        sd_client._token_expires = None
        sd_client.settings.token_cache_path.unlink(missing_ok=True)  # Ensure no cache

        await sd_client._ensure_token()

        assert sd_client._token is not None
        assert sd_client._token_expires is not None
        assert sd_client._token_expires > datetime.now(UTC).timestamp()

    @pytest.mark.asyncio
    async def test_ensure_token_triggers_authenticate_expired_token(self, sd_client):
        """Test _ensure_token triggers authenticate when cached token is expired."""
        expired_timestamp = int((datetime.now(UTC) - timedelta(days=1)).timestamp())
        sd_client._token = "expired_internal_token"
        sd_client._token_expires = expired_timestamp
        # Also write an expired token to cache to simulate a full expired scenario
        with open(sd_client.settings.token_cache_path, "w") as f:
            json.dump({"token": "expired_cached_token", "tokenExpires": expired_timestamp}, f)

        await sd_client._ensure_token()

        assert sd_client._token is not None
        assert sd_client._token != "expired_internal_token"
        assert sd_client._token_expires is not None
        assert sd_client._token_expires > datetime.now(UTC).timestamp()

    @pytest.mark.asyncio
    async def test_ensure_token_valid_token_present(self, sd_client):
        """Test _ensure_token when a valid token is already present."""
        expected_token = "already_valid_token"
        expected_expires = int((datetime.now(UTC) + timedelta(days=1)).timestamp())
        sd_client._token = expected_token
        sd_client._token_expires = expected_expires
        # Ensure cache also has a valid token
        with open(sd_client.settings.token_cache_path, "w") as f:
            json.dump({"token": expected_token, "tokenExpires": expected_expires}, f)

        await sd_client._ensure_token()

        # Token should remain unchanged
        assert sd_client._token == expected_token
        assert sd_client._token_expires == expected_expires

    # --- Base Request Method Tests ---

    @pytest.mark.asyncio
    async def test_request_successful_get(self, sd_client):
        """Test _request for a successful GET request (e.g., get_lineups)."""
        # Ensure token is present before making the request
        await sd_client._ensure_token()

        lineups = await sd_client.get_lineups()
        assert isinstance(lineups, list)
        assert len(lineups) > 0
        assert all(isinstance(lineup, UserLineup) for lineup in lineups)
        assert lineups[0].lineup is not None
        assert lineups[0].name is not None

    @pytest.mark.asyncio
    async def test_request_successful_post(self, sd_client):
        """Test _request for a successful POST request (e.g., get_schedule_md5s)."""
        # Ensure token is present before making the request
        await sd_client._ensure_token()

        # Get a lineup to extract a station ID
        lineups = await sd_client.get_lineups()
        assert len(lineups) > 0
        lineup_id = lineups[0].lineup

        lineup_stations_response = await sd_client.get_lineup_stations(lineup_id)
        assert len(lineup_stations_response.stations) > 0
        station_id = lineup_stations_response.stations[0].stationID

        # Use current date for schedule MD5s
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        md5_response = await sd_client.get_schedule_md5s(station_ids=[station_id])

        assert isinstance(md5_response, ScheduleMD5Response)
        assert station_id in md5_response.model_dump()
        assert today_str in md5_response.model_dump()[station_id]
        assert md5_response.model_dump()[station_id][today_str]["md5"] is not None

    # --- API Endpoints Tests ---

    @pytest.mark.asyncio
    async def test_get_lineups(self, sd_client):
        """Test get_lineups endpoint."""
        lineups = await sd_client.get_lineups()
        assert isinstance(lineups, list)
        assert len(lineups) > 0
        assert all(isinstance(lineup, UserLineup) for lineup in lineups)
        assert lineups[0].lineup is not None
        assert lineups[0].name is not None
        print(f"\nFound {len(lineups)} lineups. Example: {lineups[0].name}")

    @pytest.mark.asyncio
    async def test_get_lineup_stations(self, sd_client):
        """Test get_lineup_stations endpoint."""
        lineups = await sd_client.get_lineups()
        assert len(lineups) > 0
        lineup_id = lineups[0].lineup

        lineup_stations_response = await sd_client.get_lineup_stations(lineup_id)
        assert isinstance(lineup_stations_response, LineupStationsResponse)
        assert len(lineup_stations_response.stations) > 0
        assert len(lineup_stations_response.map) > 0
        assert isinstance(lineup_stations_response.stations[0].stationID, str)
        assert isinstance(lineup_stations_response.map[0].channel, str)
        print(f"Lineup '{lineup_id}' has {len(lineup_stations_response.stations)} stations.")
        print(
            f"Example station: {lineup_stations_response.stations[0].name} ({lineup_stations_response.stations[0].callsign})"
        )

    @pytest.mark.asyncio
    async def test_get_schedule_md5s(self, sd_client):
        """Test get_schedule_md5s endpoint."""
        lineups = await sd_client.get_lineups()
        assert len(lineups) > 0
        lineup_id = lineups[0].lineup

        lineup_stations_response = await sd_client.get_lineup_stations(lineup_id)
        assert len(lineup_stations_response.stations) > 0
        station_id = lineup_stations_response.stations[0].stationID

        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        tomorrow_str = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")
        dates = [today_str, tomorrow_str]

        md5_response = await sd_client.get_schedule_md5s(station_ids=[station_id])

        assert isinstance(md5_response, ScheduleMD5Response)
        assert station_id in md5_response.model_dump()
        for date_str in dates:
            assert date_str in md5_response.model_dump()[station_id]
            assert md5_response.model_dump()[station_id][date_str]["md5"] is not None
        print(f"Retrieved MD5s for station {station_id} for dates {dates}")

    @pytest.mark.asyncio
    async def test_get_schedules(self, sd_client):
        """Test get_schedules endpoint."""
        lineups = await sd_client.get_lineups()
        assert len(lineups) > 0
        lineup_id = lineups[0].lineup

        lineup_stations_response = await sd_client.get_lineup_stations(lineup_id)
        assert len(lineup_stations_response.stations) > 0
        station_id = lineup_stations_response.stations[0].stationID

        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        schedules_response = await sd_client.get_schedules(station_ids=[station_id])

        assert isinstance(schedules_response, SchedulesResponse)
        assert len(schedules_response.model_dump()) > 0
        schedule_entry = schedules_response.model_dump()[0]
        assert schedule_entry["stationID"] == station_id
        assert len(schedule_entry["programs"]) > 0
        assert isinstance(schedule_entry["programs"][0]["programID"], str)
        print(f"Retrieved schedules for station {station_id} for date {today_str}")
        print(f"Example program: {schedule_entry['programs'][0]['programID']}")

    @pytest.mark.asyncio
    async def test_get_programs(self, sd_client):
        """Test get_programs endpoint."""
        lineups = await sd_client.get_lineups()
        assert len(lineups) > 0
        lineup_id = lineups[0].lineup

        lineup_stations_response = await sd_client.get_lineup_stations(lineup_id)
        assert len(lineup_stations_response.stations) > 0
        station_id = lineup_stations_response.stations[0].stationID

        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        schedules_response = await sd_client.get_schedules(station_ids=[station_id])
        assert len(schedules_response.model_dump()) > 0
        schedule_entry = schedules_response.model_dump()[0]
        program_ids = [
            p["programID"] for p in schedule_entry["programs"][:3]
        ]  # Get first 3 program IDs

        if not program_ids:
            pytest.skip(
                f"No programs found for station {station_id} on {today_str} to test get_programs."
            )

        programs_response = await sd_client.get_programs(program_ids)

        assert isinstance(programs_response, ProgramsResponse)
        assert len(programs_response.model_dump()) == len(program_ids)
        assert all(isinstance(p["programID"], str) for p in programs_response.model_dump())
        print(f"Retrieved program details for {len(program_ids)} programs.")
        print(
            f"Example program title: {programs_response.model_dump()[0]['titles'][0]['title120']}"
        )

    @pytest.mark.asyncio
    async def test_add_lineup_if_none_exist(self, sd_client):
        """
        Test adding a lineup if the account currently has none.
        This test will only add a lineup if get_lineups returns an empty list.
        It will attempt to add a lineup for a generic US postal code.
        """
        lineups = await sd_client.get_lineups()
        if len(lineups) == 0:
            print("\nNo lineups found. Attempting to add one...")
            # Use a generic US postal code for testing
            country = "USA"
            postal_code = "90210"  # Beverly Hills, CA

            headends = await sd_client.get_headends(country, postal_code)
            assert len(headends) > 0, f"No headends found for {country}, {postal_code}"

            # Find a lineup to add (e.g., the first one available)
            selected_lineup = None
            for headend in headends:
                if headend.lineups:
                    selected_lineup = headend.lineups[0]
                    break

            assert selected_lineup is not None, (
                f"No lineups available in headends for {country}, {postal_code}"
            )

            print(f"Attempting to add lineup: {selected_lineup.lineup} ({selected_lineup.name})")
            add_response = await sd_client.add_lineup(selected_lineup.lineup)

            assert add_response.code == 0
            print(f"Successfully added lineup: {add_response.lineup}")

            # Verify the lineup now exists
            updated_lineups = await sd_client.get_lineups()
            assert len(updated_lineups) > 0
            assert any(ul.lineup == selected_lineup.lineup for ul in updated_lineups)
        else:
            print(f"\n{len(lineups)} lineups already exist. Skipping lineup addition test.")
            assert True  # Test passes if lineups already exist

    # --- Error Handling Tests ---

    def test_handle_error_response(self, sd_client):
        """Test _handle_error_response directly with various error codes."""
        # Test with a known error code
        error_data = {"code": 3000, "message": "SERVICE_OFFLINE", "serverID": "test_server"}
        with pytest.raises(SDError) as exc_info:
            sd_client._handle_error_response(error_data)
        assert exc_info.value.code == 3000
        assert exc_info.value.message == "SERVICE_OFFLINE"
        assert exc_info.value.serverID == "test_server"

        # Test with another known error code
        error_data = {
            "code": 4001,
            "message": "ACCOUNT_EXPIRED",
            "datetime": "2025-01-01T00:00:00Z",
        }
        with pytest.raises(SDError) as exc_info:
            sd_client._handle_error_response(error_data)
        assert exc_info.value.code == 4001
        assert exc_info.value.message == "ACCOUNT_EXPIRED"
        # The field_validator in SDErrorData will convert the string to datetime
        assert exc_info.value.timestamp == datetime(2025, 1, 1, 0, 0, tzinfo=UTC)

        # Test with an unknown error code (should still raise SDError)
        error_data = {"code": 9999, "message": "UNKNOWN_ERROR"}
        with pytest.raises(SDError) as exc_info:
            sd_client._handle_error_response(error_data)
        assert exc_info.value.code == 9999
        assert exc_info.value.message == "UNKNOWN_ERROR"
