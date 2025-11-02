from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, RootModel, field_validator


class SDErrorData(BaseModel):
    code: int
    message: str
    response: str | None = None
    serverID: str | None = None
    timestamp: datetime | None = Field(default=None, alias="datetime")
    token: str | None = None
    tokenExpires: int | None = None
    minDate: str | None = None
    maxDate: str | None = None
    requestedDate: str | None = None
    stationID: str | None = None
    retryTime: datetime | None = Field(default=None)

    @field_validator("timestamp", "retryTime", mode="before")
    @classmethod
    def parse_datetime_string(cls, value: Any) -> datetime | None:
        if isinstance(value, str):
            # Assuming the string is in ISO 8601 format with 'Z' for UTC
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value


class SDError(Exception):
    def __init__(self, data: SDErrorData):
        self.data = data
        super().__init__(data.message)

    def __getattr__(self, name: str):
        return getattr(self.data, name)


class TokenResponse(BaseModel):
    code: int
    message: str
    serverID: str
    datetime: datetime
    token: str
    tokenExpires: int
    serverTime: int | None = None


class AccountStatus(BaseModel):
    expires: datetime
    messages: list[str]
    maxLineups: int


class LineupStatus(BaseModel):
    lineup: str
    modified: datetime
    uri: str | None = None
    ID: str | None = None  # Sometimes ID is used instead of lineup
    isDeleted: bool | None = False


class SystemStatus(BaseModel):
    date: datetime
    status: str
    message: str


class StatusResponse(BaseModel):
    account: AccountStatus
    lineups: list[LineupStatus]
    lastDataUpdate: datetime
    notifications: list[Any]
    systemStatus: list[SystemStatus]
    serverID: str
    datetime: datetime
    code: int
    tokenExpires: int


class HeadendLineup(BaseModel):
    name: str
    lineup: str
    uri: str


class Headend(BaseModel):
    headend: str
    transport: str
    location: str
    lineups: list[HeadendLineup]


class HeadendsResponse(RootModel[list[Headend]]):
    pass


class LineupPreviewStation(BaseModel):
    channel: str
    name: str
    callsign: str
    affiliate: str | None = None


class LineupPreviewResponse(RootModel[list[LineupPreviewStation]]):
    pass


class UserLineup(BaseModel):
    lineup: str
    name: str
    transport: str
    location: str
    uri: str | None = None
    isDeleted: bool | None = False


class UserLineupsResponse(BaseModel):
    code: int
    serverID: str
    datetime: datetime
    lineups: list[UserLineup]


class AddLineupRequest(BaseModel):
    lineup: str


class AddLineupResponse(BaseModel):
    code: int
    response: str
    message: str
    serverID: str
    datetime: datetime
    changesRemaining: int


class DeleteLineupResponse(BaseModel):
    code: int
    response: str
    message: str
    serverID: str
    datetime: datetime
    changesRemaining: int


class StationLogo(BaseModel):
    URL: str
    height: int
    width: int
    md5: str
    source: str | None = None
    category: str | None = None


class Broadcaster(BaseModel):
    city: str
    state: str | None = None
    postalcode: str | None = None
    country: str


class LineupStation(BaseModel):
    stationID: str
    name: str
    callsign: str
    affiliate: str | None = None
    broadcastLanguage: list[str] | None = None
    descriptionLanguage: list[str] | None = None
    broadcaster: Broadcaster | None = None
    isCommercialFree: bool | None = False
    stationLogo: list[StationLogo] | None = None
    logo: StationLogo | None = None  # Deprecated


class LineupMapEntry(BaseModel):
    stationID: str
    channel: str
    uhfVhf: int | None = None
    atscMajor: int | None = None
    atscMinor: int | None = None
    providerCallsign: str | None = None
    logicalChannelNumber: str | None = None
    matchType: str | None = None
    frequencyHz: int | None = None
    serviceID: int | None = None
    networkID: int | None = None
    transportID: int | None = None
    deliverySystem: str | None = None
    modulationSystem: str | None = None
    symbolrate: int | None = None
    polarization: str | None = None
    fec: str | None = None
    virtualChannel: str | None = None
    channelMajor: int | None = None
    channelMinor: int | None = None


class LineupMetadata(BaseModel):
    lineup: str
    modified: datetime
    transport: str
    modulation: str | None = None


class LineupStationsResponse(BaseModel):
    map: list[LineupMapEntry]
    stations: list[LineupStation]
    metadata: LineupMetadata


class ProgramTitle(BaseModel):
    title120: str
    titleLanguage: str | None = None


class ProgramDescription(BaseModel):
    descriptionLanguage: str
    description: str


class ProgramDescriptions(BaseModel):
    description1000: list[ProgramDescription] | None = None
    description100: list[ProgramDescription] | None = None


class ProgramMetadataEntry(BaseModel):
    season: int | None = None
    episode: int | None = None
    totalEpisodes: int | None = None
    totalSeasons: int | None = None
    url: str | None = None  # For TVmaze


class ProgramMetadata(BaseModel):
    Gracenote: ProgramMetadataEntry | None = None
    TVmaze: ProgramMetadataEntry | None = None


class CastCrewMember(BaseModel):
    billingOrder: str
    role: str
    name: str
    characterName: str | None = None
    nameId: str | None = None
    personId: str | None = None


class ContentRating(BaseModel):
    body: str
    code: str
    country: str | None = None
    contentWarning: list[str] | None = None


class MovieQualityRating(BaseModel):
    ratingsBody: str
    rating: str
    minRating: str | None = None
    maxRating: str | None = None
    increment: str | None = None


class MovieInfo(BaseModel):
    year: str | None = None
    duration: int | None = None
    qualityRating: list[MovieQualityRating] | None = None


class MultiPart(BaseModel):
    partNumber: int
    totalParts: int


class ProgramResponse(BaseModel):
    programID: str
    resourceID: str | None = None
    titles: list[ProgramTitle]
    descriptions: ProgramDescriptions | None = None
    originalAirDate: str | None = None
    showType: str | None = None
    entityType: str
    country: list[str] | None = None
    genres: list[str] | None = None
    cast: list[CastCrewMember] | None = None
    crew: list[CastCrewMember] | None = None
    episodeTitle150: str | None = None
    duration: int | None = None
    metadata: list[dict[str, ProgramMetadataEntry]] | None = None
    hasImageArtwork: bool | None = False
    hasEpisodeArtwork: bool | None = False
    hasSeasonArtwork: bool | None = False
    hasSeriesArtwork: bool | None = False
    hasMovieArtwork: bool | None = False
    hasSportsArtwork: bool | None = False
    hash: str | None = None
    md5: str
    contentAdvisory: list[str] | None = None
    contentRating: list[ContentRating] | None = None
    movie: MovieInfo | None = None
    officialURL: str | None = None
    multiPart: MultiPart | None = None
    eventDetails: dict[str, Any] | None = None  # Too complex to model fully for now


class ProgramsResponse(RootModel[list[ProgramResponse]]):
    pass


class ScheduleMD5Entry(BaseModel):
    code: int
    message: str = "OK"
    lastModified: datetime
    md5: str


class ScheduleMD5Response(RootModel[dict[str, dict[str, ScheduleMD5Entry]]]):
    pass


class ScheduleProgram(BaseModel):
    programID: str
    airDateTime: datetime
    duration: int
    md5: str
    new: bool | None = False
    cableInTheClassroom: bool | None = False
    catchup: bool | None = False
    continued: bool | None = False
    educational: bool | None = False
    joinedInProgress: bool | None = False
    leftInProgress: bool | None = False
    premiere: bool | None = False
    programBreak: bool | None = False
    repeat: bool | None = False
    signed: bool | None = False
    subjectToBlackout: bool | None = False
    timeApproximate: bool | None = False
    free: bool | None = False
    liveTapeDelay: str | None = None
    isPremiereOrFinale: str | None = None
    ratings: list[ContentRating] | None = None
    multiPart: MultiPart | None = None
    audioProperties: list[str] | None = None
    videoProperties: list[str] | None = None


class ScheduleMetadata(BaseModel):
    modified: datetime
    md5: str
    startDate: str
    code: int | None = None
    isDeleted: bool | None = False


class ScheduleEntry(BaseModel):
    stationID: str
    programs: list[ScheduleProgram]
    metadata: ScheduleMetadata


class SchedulesResponse(RootModel[list[ScheduleEntry]]):
    pass
