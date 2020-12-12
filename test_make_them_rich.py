import base64
import json

from make_them_rich import handle_event


def build_event(body):
    return {
        'body': base64.encodebytes(json.dumps(body).encode('utf8')).decode('utf8')
    }


def test_handler():
    handle_event(None, None)


def test_handler_not_returns_verification_code_when_confirmation_event_not_occurs(monkeypatch):
    monkeypatch.setenv('VERIFICATION_CODE', '123456')

    event = build_event({'type': 'some-strange-event'})

    result = handle_event(event, None)
    assert result['statusCode'] == 422


def test_handler_returns_verification_code_only_when_confirmation_event_occurs(monkeypatch):
    monkeypatch.setenv('VERIFICATION_CODE', '123456')

    event = build_event({'type': 'confirmation'})

    result = handle_event(event, None)
    assert result['body'] == '123456'
    assert result['statusCode'] == 200


def test_handle_like_add():
    event = build_event({
        "type": "like_add",
        "object": {
            "liker_id": 343298673,
            "object_type": "post",
            "object_owner_id": -201077021,
            "object_id": 7,
            "thread_reply_id": 0,
            "post_id": 0
        },
        "group_id": 201077021,
        "event_id": "1e16f5efa7cd639eba2c677571dc5f5a5ee21780"
    })

    result = handle_event(event, None)
    assert result['body'] is 'ok'
    assert result['statusCode'] == 200


def test_handle_wall_reply_new():
    event = build_event({
        "type": "wall_reply_new",
        "object": {
            "id": 8,
            "from_id": 343298673,
            "date": 1607801025,
            "text": "Привет! Сколько стоит пицца карбонара без лука?",
            "post_owner_id": -201077021,
            "post_id": 5
        },
        "group_id": 201077021,
        "event_id": "46e87d9c892ee9265959eb40efb9e55e61f9f768"
    })

    result = handle_event(event, None)
    assert result['body'] is 'ok'
    assert result['statusCode'] == 200

# todo test with a database...
