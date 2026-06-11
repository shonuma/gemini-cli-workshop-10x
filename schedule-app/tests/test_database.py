import datetime
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time

from database import (create_new_event, delete_event_from_db,
                      delete_response_from_db, get_all_events,
                      get_event_and_responses, save_new_response)
from models import EventCreateRequest, ResponseModel


@pytest.fixture
def mock_db_client(mocker):
    """A fixture to mock the Firestore client in the database module."""
    return mocker.patch('database._get_db').return_value


def test_get_all_events_with_sorting(mock_db_client):
    """
    created_at の有無や値に基づいてイベントが正しくソートされるかをテスト
    """
    mock_event_1 = MagicMock()
    mock_event_1.id = "event1"
    mock_event_1.to_dict.return_value = {
        'name': 'Event 1',
        'created_at': datetime.datetime(2023, 1, 1)
    }

    mock_event_2 = MagicMock()
    mock_event_2.id = "event2"
    mock_event_2.to_dict.return_value = {'name': 'Event 2 (no date)'}

    mock_event_3 = MagicMock()
    mock_event_3.id = "event3"
    mock_event_3.to_dict.return_value = {
        'name': 'Event 3',
        'created_at': datetime.datetime(2023, 1, 2)
    }

    mock_db_client.collection.return_value.stream.return_value = [
        mock_event_1, mock_event_2, mock_event_3
    ]

    mock_doc_event1 = MagicMock()
    # 2 responses
    mock_doc_event1.collection.return_value.stream.return_value = iter(
        [MagicMock(), MagicMock()]
    )
    mock_doc_event2 = MagicMock()
    # 0 responses
    mock_doc_event2.collection.return_value.stream.return_value = iter([])
    mock_doc_event3 = MagicMock()
    # 1 response
    mock_doc_event3.collection.return_value.stream.return_value = iter(
        [MagicMock()]
    )

    def doc_side_effect(doc_id):
        if doc_id == "event1":
            return mock_doc_event1
        if doc_id == "event2":
            return mock_doc_event2
        if doc_id == "event3":
            return mock_doc_event3
        return MagicMock()

    mock_db_client.collection.return_value.document.side_effect = doc_side_effect

    events = get_all_events()

    assert len(events) == 3
    assert events[0]['id'] == 'event3' and events[0]['responses_count'] == 1
    assert events[1]['id'] == 'event1' and events[1]['responses_count'] == 2
    assert events[2]['id'] == 'event2' and events[2]['responses_count'] == 0


@freeze_time("2023-01-15 12:00:00")
def test_create_new_event(mock_db_client):
    """
    新しいイベントが正しいデータで作成されるかをテスト
    """
    event_req = EventCreateRequest(
        **{"event-name": "Test", "candidate-dates": ["2023-01-20"], "password": "1234"}
    )
    mock_event_ref = mock_db_client.collection.return_value.document.return_value

    with patch('uuid.uuid4', return_value='test-uuid'):
        event_id = create_new_event(event_req)

    assert event_id == 'test-uuid'
    mock_db_client.collection.assert_called_with('events')
    mock_db_client.collection.return_value.document.assert_called_with('test-uuid')

    set_data = mock_event_ref.set.call_args[0][0]
    assert set_data['name'] == "Test"
    assert set_data['created_at'] == datetime.datetime(2023, 1, 15, 12)
    assert 'password_hash' in set_data


def test_get_event_and_responses_not_found(mock_db_client):
    """
    存在しない event_id を指定した際に None が返ることをテスト
    """
    mock_event_snap = MagicMock()
    mock_event_snap.exists = False
    mock_db_client.collection.return_value.document.return_value \
        .get.return_value = mock_event_snap

    result = get_event_and_responses("nonexistent-id")

    assert result is None


def test_save_new_response_create(mock_db_client):
    """
    新しい回答を保存するテスト
    """
    resp_data = ResponseModel(name="User", availability={"2023-01-20": "○"})
    mock_responses_ref = mock_db_client.collection.return_value.document \
        .return_value.collection.return_value

    save_new_response("event-id", resp_data)

    mock_responses_ref.add.assert_called_once()


def test_delete_response_from_db(mock_db_client):
    """
    回答を削除するテスト
    """
    mock_resp_ref = mock_db_client.collection.return_value.document \
        .return_value.collection.return_value.document.return_value
    mock_resp_ref.get.return_value.exists = True

    delete_response_from_db("event-id", "resp-id")

    mock_resp_ref.delete.assert_called_once()


def test_delete_event_from_db_success(mock_db_client):
    """
    正しいパスワードでイベントを削除するテスト
    """
    from werkzeug.security import generate_password_hash
    password = "1234"
    hashed = generate_password_hash(password)

    mock_event_ref = mock_db_client.collection.return_value.document.return_value
    mock_event_snap = mock_event_ref.get.return_value
    mock_event_snap.exists = True
    mock_event_snap.to_dict.return_value = {
        'name': 'Test',
        'candidate_dates': [],
        'password_hash': hashed,
        'created_at': None
    }

    mock_responses_ref = mock_event_ref.collection.return_value
    mock_responses_ref.stream.return_value = []

    delete_event_from_db("event-id", password)

    mock_event_ref.delete.assert_called_once()


def test_delete_event_from_db_wrong_password(mock_db_client):
    """
    間違ったパスワードでイベント削除に失敗するテスト
    """
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash("1234")

    mock_event_ref = mock_db_client.collection.return_value.document.return_value
    mock_event_snap = mock_event_ref.get.return_value
    mock_event_snap.exists = True
    mock_event_snap.to_dict.return_value = {
        'name': 'Test',
        'candidate_dates': [],
        'password_hash': hashed,
        'created_at': None
    }

    with pytest.raises(ValueError, match="パスワードが違います"):
        delete_event_from_db("event-id", "wrong")
