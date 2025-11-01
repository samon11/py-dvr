from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, RootModel, field_validator


class SDErrorData(BaseModel):
    code: int
    message: str
    response: Optional[str] = None
    serverID: Optional[str] = None
    timestamp: Optional[datetime] = Field(default=None, alias="datetime")
    token: Optional[str] = None
    tokenExpires: Optional[int] = None
    minDate: Optional[str] = None
    maxDate: Optional[str] = None
    requestedDate: Optional[str] = None
    stationID: Optional[str] = None
    retryTime: Optional[datetime] = Field(default=None)

    @field_validator('timestamp', 'retryTime', mode='before')
    @classmethod
    def parse_datetime_string(cls, value: Any) -> Optional[datetime]:
        if isinstance(value, str):
            # Assuming the string is in ISO 8601 format with 'Z' for UTC
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
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
    serverTime: Optional[int] = None


class AccountStatus(BaseModel):
    expires: datetime
    messages: List[str]
    maxLineups: int


class LineupStatus(BaseModel):
    lineup: str
    modified: datetime
    uri: Optional[str] = None
    ID: Optional[str] = None  # Sometimes ID is used instead of lineup
    isDeleted: Optional[bool] = False


class SystemStatus(BaseModel):
    date: datetime
    status: str
    message: str


class StatusResponse(BaseModel):
    account: AccountStatus
    lineups: List[LineupStatus]
    lastDataUpdate: datetime
    notifications: List[Any]
    systemStatus: List[SystemStatus]
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
    lineups: List[HeadendLineup]


class HeadendsResponse(RootModel[List[Headend]]):
    pass


class LineupPreviewStation(BaseModel):
    channel: str
    name: str
    callsign: str
    affiliate: Optional[str] = None


class LineupPreviewResponse(RootModel[List[LineupPreviewStation]]):
    pass


class UserLineup(BaseModel):
    lineup: str
    name: str
    transport: str
    location: str
    uri: Optional[str] = None
    isDeleted: Optional[bool] = False


class UserLineupsResponse(BaseModel):
    code: int
    serverID: str
    datetime: datetime
    lineups: List[UserLineup]


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
    source: Optional[str] = None
    category: Optional[str] = None


class Broadcaster(BaseModel):
    city: str
    state: Optional[str] = None
    postalcode: Optional[str] = None
    country: str


class LineupStation(BaseModel):
    stationID: str
    name: str
    callsign: str
    affiliate: Optional[str] = None
    broadcastLanguage: Optional[List[str]] = None
    descriptionLanguage: Optional[List[str]] = None
    broadcaster: Optional[Broadcaster] = None
    isCommercialFree: Optional[bool] = False
    stationLogo: Optional[List[StationLogo]] = None
    logo: Optional[StationLogo] = None  # Deprecated


class LineupMapEntry(BaseModel):
    stationID: str
    channel: str
    uhfVhf: Optional[int] = None
    atscMajor: Optional[int] = None
    atscMinor: Optional[int] = None
    providerCallsign: Optional[str] = None
    logicalChannelNumber: Optional[str] = None
    matchType: Optional[str] = None
    frequencyHz: Optional[int] = None
    serviceID: Optional[int] = None
    networkID: Optional[int] = None
    transportID: Optional[int] = None
    deliverySystem: Optional[str] = None
    modulationSystem: Optional[str] = None
    symbolrate: Optional[int] = None
    polarization: Optional[str] = None
    fec: Optional[str] = None
    virtualChannel: Optional[str] = None
    channelMajor: Optional[int] = None
    channelMinor: Optional[int] = None


class LineupMetadata(BaseModel):
    lineup: str
    modified: datetime
    transport: str
    modulation: Optional[str] = None


class LineupStationsResponse(BaseModel):
    map: List[LineupMapEntry]
    stations: List[LineupStation]
    metadata: LineupMetadata


class ProgramTitle(BaseModel):
    title120: str
    titleLanguage: Optional[str] = None


class ProgramDescription(BaseModel):
    descriptionLanguage: str
    description: str


class ProgramDescriptions(BaseModel):
    description1000: Optional[List[ProgramDescription]] = None
    description100: Optional[List[ProgramDescription]] = None


class ProgramMetadataEntry(BaseModel):
    season: Optional[int] = None
    episode: Optional[int] = None
    totalEpisodes: Optional[int] = None
    totalSeasons: Optional[int] = None
    url: Optional[str] = None # For TVmaze


class ProgramMetadata(BaseModel):
    Gracenote: Optional[ProgramMetadataEntry] = None
    TVmaze: Optional[ProgramMetadataEntry] = None


class CastCrewMember(BaseModel):
    billingOrder: str
    role: str
    name: str
    characterName: Optional[str] = None
    nameId: Optional[str] = None
    personId: Optional[str] = None


class ContentRating(BaseModel):
    body: str
    code: str
    country: Optional[str] = None
    contentWarning: Optional[List[str]] = None


class MovieQualityRating(BaseModel):
    ratingsBody: str
    rating: str
    minRating: Optional[str] = None
    maxRating: Optional[str] = None
    increment: Optional[str] = None


class MovieInfo(BaseModel):
    year: Optional[str] = None
    duration: Optional[int] = None
    qualityRating: Optional[List[MovieQualityRating]] = None


class MultiPart(BaseModel):
    partNumber: int
    totalParts: int


class ProgramResponse(BaseModel):
    programID: str
    resourceID: Optional[str] = None
    titles: List[ProgramTitle]
    descriptions: Optional[ProgramDescriptions] = None
    originalAirDate: Optional[str] = None
    showType: Optional[str] = None
    entityType: str
    country: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    cast: Optional[List[CastCrewMember]] = None
    crew: Optional[List[CastCrewMember]] = None
    episodeTitle150: Optional[str] = None
    duration: Optional[int] = None
    metadata: Optional[List[Dict[str, ProgramMetadata]]] = None
    hasImageArtwork: Optional[bool] = False
    hasEpisodeArtwork: Optional[bool] = False
    hasSeasonArtwork: Optional[bool] = False
    hasSeriesArtwork: Optional[bool] = False
    hasMovieArtwork: Optional[bool] = False
    hasSportsArtwork: Optional[bool] = False
    hash: Optional[str] = None
    md5: str
    contentAdvisory: Optional[List[str]] = None
    contentRating: Optional[List[ContentRating]] = None
    movie: Optional[MovieInfo] = None
    officialURL: Optional[str] = None
    multiPart: Optional[MultiPart] = None
    eventDetails: Optional[Dict[str, Any]] = None # Too complex to model fully for now


class ProgramsResponse(RootModel[List[ProgramResponse]]):
    pass


class ScheduleMD5Entry(BaseModel):
    code: int
    message: str = "OK"
    lastModified: datetime
    md5: str


class ScheduleMD5Response(RootModel[Dict[str, Dict[str, ScheduleMD5Entry]]]):
    pass


class ScheduleProgram(BaseModel):
    programID: str
    airDateTime: datetime
    duration: int
    md5: str
    new: Optional[bool] = False
    cableInTheClassroom: Optional[bool] = False
    catchup: Optional[bool] = False
    continued: Optional[bool] = False
    educational: Optional[bool] = False
    joinedInProgress: Optional[bool] = False
    leftInProgress: Optional[bool] = False
    premiere: Optional[bool] = False
    programBreak: Optional[bool] = False
    repeat: Optional[bool] = False
    signed: Optional[bool] = False
    subjectToBlackout: Optional[bool] = False
    timeApproximate: Optional[bool] = False
    free: Optional[bool] = False
    liveTapeDelay: Optional[str] = None
    isPremiereOrFinale: Optional[str] = None
    ratings: Optional[List[ContentRating]] = None
    multiPart: Optional[MultiPart] = None
    audioProperties: Optional[List[str]] = None
    videoProperties: Optional[List[str]] = None


class ScheduleMetadata(BaseModel):
    modified: datetime
    md5: str
    startDate: str
    code: Optional[int] = None
    isDeleted: Optional[bool] = False


class ScheduleEntry(BaseModel):
    stationID: str
    programs: List[ScheduleProgram]
    metadata: ScheduleMetadata


class SchedulesResponse(RootModel[List[ScheduleEntry]]):
    pass