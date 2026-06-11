import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from constants import Availability


class ResponseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(default=None, alias="response_id")
    name: str
    availability: dict[str, Availability]


class EventModel(BaseModel):
    name: str
    description: str = ""
    candidate_dates: list[str]
    password_hash: str
    created_at: Optional[datetime.datetime]


class EventDetailResult(BaseModel):
    event_data: EventModel
    candidate_dates: list[str]
    responses: list[dict]
    date_scores: dict[str, float]
    best_dates: list[str]


class EventCreateRequest(BaseModel):
    name: str = Field(alias="event-name")
    description: str = ""
    candidate_dates: list[str] = Field(alias="candidate-dates")
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not (v.isdigit() and len(v) == 4):
            raise ValueError('パスワードは4桁の数字である必要があります。')
        return v
