import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pydvr.config import get_settings
from pydvr.schemas.schedules_direct import (
    AddLineupRequest,
    AddLineupResponse,
    DeleteLineupResponse,
    Headend,
    LineupStationsResponse,
    ProgramsResponse,
    ScheduleMD5Response,
    SchedulesResponse,
    SDError,
    SDErrorData,
    TokenResponse,
    UserLineup,
)

logger = logging.getLogger(__name__)


class SchedulesDirectClient:
    """Client for Schedules Direct JSON API v20141201"""

    BASE_URL = "https://json.schedulesdirect.org/20141201"

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(timeout=600.0)  # 10-minute timeout
        self._token: str | None = None
        self._token_expires: int | None = None

    # Token Management
    async def _get_cached_token(self) -> tuple[str, int] | None:
        """Load token from file cache if valid"""
        cache_path = self.settings.token_cache_path
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
            token = data.get("token")
            expires = data.get("tokenExpires")
            if token and expires and expires > datetime.now(UTC).timestamp():
                return token, expires
        except (OSError, json.JSONDecodeError):
            # Cache file is corrupt or unreadable, treat as no cache
            pass
        return None

    async def _save_token(self, token: str, expires: int) -> None:
        """Save token to file cache"""
        cache_path = self.settings.token_cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump({"token": token, "tokenExpires": expires}, f)

    async def authenticate(self) -> TokenResponse:
        """Authenticate and return token (POST /token)"""
        # Check cache first
        cached = await self._get_cached_token()
        if cached and cached[1] > datetime.now(UTC).timestamp():
            self._token, self._token_expires = cached
            return TokenResponse(
                token=self._token,
                tokenExpires=self._token_expires,
                code=0,
                message="OK",
                serverID="cached",
                datetime=datetime.now(UTC),
            )

        logger.debug("Attempting to authenticate with Schedules Direct API.")
        logger.debug(f"SD_USERNAME: {self.settings.sd_username}")
        # Do not log the password for security reasons

        password_hash = hashlib.sha1(self.settings.sd_password.encode()).hexdigest()

        try:
            response = await self.client.post(
                f"{self.BASE_URL}/token",
                json={"username": self.settings.sd_username, "password": password_hash},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            data = response.json()
            logger.debug(f"Schedules Direct authentication response: {data}")

            if data.get("code") != 0:
                self._handle_error_response(data)

            token_response = TokenResponse(**data)
            # Cache token
            self._token = token_response.token
            self._token_expires = token_response.tokenExpires
            await self._save_token(self._token, self._token_expires)

            return token_response
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error during authentication: {e}")
            # Attempt to parse error response from Schedules Direct if available
            try:
                error_data = e.response.json()
                self._handle_error_response(error_data)
            except json.JSONDecodeError:
                # If response is not JSON, create a generic error
                self._handle_error_response(
                    {"code": e.response.status_code, "message": str(e), "response": e.response.text}
                )
            raise
        except httpx.RequestError as e:
            logger.error(f"Request Error during authentication: {e}")
            self._handle_error_response({"code": -1, "message": str(e)})
            raise

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token, refresh if needed"""
        if (
            self._token is None
            or self._token_expires is None
            or self._token_expires <= datetime.now(UTC).timestamp()
        ):
            await self.authenticate()

    # Base Request Method
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.RequestError),
    )
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Base method with token header, error handling, retry logic"""
        await self._ensure_token()
        headers = kwargs.pop("headers", {})
        headers["token"] = self._token
        headers["User-agent"] = "PyHDHrDVR/1.0"

        # Only set Content-Type for methods that typically have a body
        if method in ["POST", "PUT", "PATCH"]:
            headers["Content-Type"] = "application/json"

        request_url = f"{self.BASE_URL}{endpoint}"
        logger.debug(f"Making {method} request to {request_url}")
        logger.debug(f"Request headers: {headers}")
        if "json" in kwargs:
            logger.debug(f"Request JSON body: {kwargs['json']}")
        elif "data" in kwargs:
            logger.debug(f"Request data body: {kwargs['data']}")

        try:
            response = await self.client.request(method, request_url, headers=headers, **kwargs)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response text: {response.text}")
            data = response.json()  # Parse JSON first to check for SD specific errors

            if isinstance(data, dict) and "code" in data and data["code"] != 0:
                self._handle_error_response(data)
            else:
                response.raise_for_status()  # Raise for non-SD errors

            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Status Error for {method} {request_url}: {e}")
            logger.error(f"Response content: {e.response.text}")
            if e.response.status_code in [401, 403]:
                # Token might be expired or invalid, try to re-authenticate
                self._token = None
                self._token_expires = None
                await self._ensure_token()
                # Re-raise to trigger retry if configured, or fail if no retries left
                raise
            raise
        except httpx.RequestError as e:
            logger.error(f"Request Error for {method} {request_url}: {e}")
            # Re-raise to trigger tenacity retry
            raise

    # API Endpoints
    async def get_lineups(self) -> list[UserLineup]:
        """GET /lineups - Get user's lineups"""
        response_data = await self._request("GET", "/lineups")
        return [UserLineup(**lineup) for lineup in response_data.get("lineups", [])]

    async def get_lineup_stations(self, lineup_id: str) -> LineupStationsResponse:
        """GET /lineups/{lineup_id} - Get stations in lineup"""
        response_data = await self._request("GET", f"/lineups/{lineup_id}")
        return LineupStationsResponse(**response_data)

    async def get_schedule_md5s(
        self,
        station_ids: list[str],
    ) -> ScheduleMD5Response:
        """POST /schedules/md5 - Check for schedule changes"""
        response_data = await self._request(
            "POST", "/schedules/md5", json=[{"stationID": sid} for sid in station_ids]
        )
        return ScheduleMD5Response.model_validate(response_data)

    async def get_schedules(self, station_ids: list[dict]) -> SchedulesResponse:
        """POST /schedules - Get schedules (batch, max 5000 stations)"""
        response_data = await self._request("POST", "/schedules", json=station_ids)
        return SchedulesResponse.model_validate(response_data)

    async def get_programs(self, program_ids: list[str]) -> ProgramsResponse:
        """POST /programs - Get program metadata (batch, max 5000)"""
        response_data = await self._request("POST", "/programs", json=program_ids)
        return ProgramsResponse.model_validate(response_data)

    async def get_headends(self, country: str, postal_code: str) -> list[Headend]:
        """GET /headends - Get available headends for a given country and postal code."""
        response_data = await self._request(
            "GET", f"/headends?country={country}&postalcode={postal_code}"
        )
        return [Headend(**headend) for headend in response_data]

    async def add_lineup(self, lineup_id: str) -> AddLineupResponse:
        """PUT /lineups/{lineupID} - Add a lineup to the user's account."""
        response_data = await self._request(
            "PUT", f"/lineups/{lineup_id}", json=AddLineupRequest(lineup=lineup_id).model_dump()
        )
        return AddLineupResponse(**response_data)

    async def delete_lineup(self, lineup_id: str) -> DeleteLineupResponse:
        """DELETE /lineups/{lineup_id} - Delete a lineup from user's account."""
        response_data = await self._request("DELETE", f"/lineups/{lineup_id}")
        return DeleteLineupResponse(**response_data)

    # Error Handling
    ERROR_CODES = {
        3000: "SERVICE_OFFLINE",
        4001: "ACCOUNT_EXPIRED",
        4005: "ACCOUNT_ACCESS_DISABLED",
        4006: "TOKEN_EXPIRED",
        4009: "TOO_MANY_LOGINS",
        4102: "NO_LINEUPS",  # Added for clarity, though handled in _handle_error_response
        6000: "INVALID_PROGRAM_ID",
        6001: "PROGRAM_QUEUED",
        7020: "SCHEDULE_RANGE_EXCEEDED",
        7100: "SCHEDULE_QUEUED",
    }

    def _handle_error_response(self, response: dict) -> None:
        """Map SD error codes to exceptions"""
        # Special handling for NO_LINEUPS error (code 4102)
        if response.get("code") == 4102:
            logger.info(
                "Schedules Direct API returned 'NO_LINEUPS' (code 4102). "
                "This is expected for accounts without configured lineups."
            )
            return  # Do not raise an error, allow processing to continue

        error_data = SDErrorData(**response)
        raise SDError(error_data)
