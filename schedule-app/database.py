import datetime
import logging
import os
import uuid
from typing import Any

from google.cloud import firestore
from werkzeug.security import check_password_hash, generate_password_hash

from models import (EventCreateRequest, EventDetailResult, EventModel,
                    ResponseModel)

# Logging configuration
logger = logging.getLogger(__name__)

# Firestore Client initialization
# The client is lazily initialized via _get_db() to avoid issues during testing
# or in environments where credentials are not immediately available.
_db_client = None


def _get_db() -> firestore.Client:
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(
            project=os.getenv('PROJECT_ID'),
            database=os.getenv('FIRESTORE_DATABASE', 'schedule-app')
        )
    return _db_client


def get_all_events() -> list[dict[str, Any]]:
    events_ref = _get_db().collection('events').stream()
    events_with_responses = []
    for event_snap in events_ref:
        event_data = event_snap.to_dict()
        if event_data:
            event_data['id'] = event_snap.id

            res_ref = _get_db().collection('events')\
                .document(event_snap.id).collection('responses')
            responses_count = len(list(res_ref.stream()))
            event_data['responses_count'] = responses_count

            events_with_responses.append(event_data)

    sorted_events = sorted(
        events_with_responses,
        key=lambda x: (x.get('created_at') is not None, x.get('created_at')),
        reverse=True
    )
    return sorted_events


def create_new_event(event_req: EventCreateRequest) -> str:
    hashed_password = generate_password_hash(event_req.password)
    event_id = str(uuid.uuid4())

    event_data = EventModel(
        name=event_req.name,
        description=event_req.description,
        candidate_dates=sorted(list(set(event_req.candidate_dates))),
        password_hash=hashed_password,
        created_at=datetime.datetime.now()
    )

    event_ref = _get_db().collection('events').document(event_id)
    event_ref.set(event_data.model_dump())
    return event_id


def get_event_and_responses(event_id: str) -> EventDetailResult | None:
    event_ref = _get_db().collection('events').document(event_id)
    event_snap = event_ref.get()

    if not event_snap.exists:
        return None

    event_dict = event_snap.to_dict()
    if not event_dict:
        return None

    event_data = EventModel.model_validate(event_dict)
    candidate_dates = event_data.candidate_dates

    responses_ref = event_ref.collection('responses')
    responses_docs = responses_ref.stream()

    responses: list[ResponseModel] = []
    responses_by_id: dict[str, dict[str, Any]] = {}

    for doc in responses_docs:
        raw_data = doc.to_dict()
        if raw_data:
            raw_data['id'] = doc.id
            resp_model = ResponseModel.model_validate(raw_data)
            responses.append(resp_model)
            responses_by_id[doc.id] = resp_model.model_dump()

    date_scores: dict[str, float] = {date: 0.0 for date in candidate_dates}
    for response in responses:
        for date, status in response.availability.items():
            if date in date_scores:
                if status == '○':
                    date_scores[date] += 1.0
                elif status == '△':
                    date_scores[date] += 0.5

    best_dates: list[str] = []
    if responses:
        max_score = max(date_scores.values()) if date_scores else 0.0
        if max_score > 0:
            best_dates = [
                date for date, score in date_scores.items() if score == max_score
            ]

    return EventDetailResult(
        event_data=event_data,
        candidate_dates=candidate_dates,
        responses=[r.model_dump() for r in responses],
        date_scores=date_scores,
        best_dates=best_dates
    )


def save_new_response(event_id: str, resp_data: ResponseModel) -> None:
    response_id = resp_data.id
    event_ref = _get_db().collection('events').document(event_id)
    responses_ref = event_ref.collection('responses')

    save_data = resp_data.model_dump(exclude={'id'})

    if response_id:
        response_ref = responses_ref.document(response_id)
        if not response_ref.get().exists:
            raise ValueError('更新対象の回答が見つかりません。')
        response_ref.update(save_data)
    else:
        responses_ref.add(save_data)


def delete_response_from_db(event_id: str, response_id: str) -> None:
    event_ref = _get_db().collection('events').document(event_id)
    response_ref = event_ref.collection('responses').document(response_id)

    if not response_ref.get().exists:
        raise ValueError('回答が見つかりません。')

    response_ref.delete()


def delete_event_from_db(event_id: str, password: str) -> None:
    event_ref = _get_db().collection('events').document(event_id)
    event_snap = event_ref.get()

    if not event_snap.exists:
        raise ValueError('イベントが見つかりません。')

    event_dict = event_snap.to_dict()
    if not event_dict:
        raise ValueError('イベントデータが不正です。')

    event_data = EventModel.model_validate(event_dict)

    if not check_password_hash(event_data.password_hash, password):
        raise ValueError('パスワードが違います。イベントを削除できません。')

    if not (password.isdigit() and len(password) == 4):
        raise ValueError('パスワードは4桁の数字である必要があります。')

    responses_ref = event_ref.collection('responses')
    for doc in responses_ref.stream():
        doc.reference.delete()

    event_ref.delete()
