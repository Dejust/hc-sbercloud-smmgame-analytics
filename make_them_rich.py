import base64
import json
import logging
import os
from datetime import datetime

import psycopg2
from psycopg2.extras import DictCursor

logger = logging.getLogger(__name__)


def get_422(err=None):
    return {
        "statusCode": 422,
        "isBase64Encoded": False,
        "body": err or 'Request payload seems wrong',
        "headers": {
            "Content-Type": "text/plain"
        }
    }


def get_200(body=None):
    return {
        "statusCode": 200,
        "isBase64Encoded": False,
        "body": body or 'ok',
        "headers": {
            "Content-Type": "text/plain"
        }
    }


def handle_event(event, context):
    if not event:
        return get_422('Unexpected event')

    body = event.get('body')

    if body is None:
        return get_422()

    parsed_body = base64.decodebytes(body.encode('utf8'))
    try:
        parsed_body = json.loads(parsed_body)
    except json.JSONDecodeError:
        return get_422('Request payload contains invalid JSON')

    event_type = parsed_body.get('type')

    if event_type == 'confirmation':
        return get_200(os.environ.get('VERIFICATION_CODE', None))
    elif event_type == 'like_add':
        object_type = parsed_body.get('object', {}).get('object_type')
        if object_type == 'post':
            _process_like(parsed_body)
            return get_200()
        else:
            return get_200()
    elif event_type == 'wall_reply_new':
        _process_comment(parsed_body)
        return get_200()

    return get_422()


def _process_like(body):
    db = None

    try:
        db = _get_db()
        cursor = db.cursor()

        group_id = body['group_id']
        settings = _get_score_settings(db, group_id)
        if settings is None:
            logger.error(f'Settings for {group_id} not found.')
            return

        cursor.execute(
            'INSERT INTO '
            'api_scoretransaction '
            '(user_id, group_id, activity_type, score, created, updated ) '
            'VALUES (%s, %s, %s, %s, %s, %s);',

            (
                body['object']['liker_id'],
                group_id,
                'like',
                settings['score_by_likes'],
                datetime.utcnow(),
                datetime.utcnow()
            )
        )
    finally:
        if db:
            db.commit()
            db.close()


def _process_comment(body):
    db = None

    try:
        db = _get_db()
        group_id = body['group_id']
        settings = _get_score_settings(db, group_id)

        if settings is None:
            logger.error(f'Settings for {group_id} not found.')
            return

        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO '
            'api_scoretransaction '
            '(user_id, group_id, activity_type, score, created, updated ) '
            'VALUES (%s, %s, %s, %s, %s, %s);',

            (
                body['object']['from_id'],
                group_id,
                'comment',
                settings['score_by_comments'],
                datetime.utcnow(),
                datetime.utcnow()
            )
        )
    finally:
        if db:
            db.commit()
            db.close()


def _get_db():
    return psycopg2.connect(
        f'dbname={os.environ["POSTGRES_DB"]} '
        f'user={os.environ["POSTGRES_USER"]} '
        f'password={os.environ["POSTGRES_PASSWORD"]} '
        f'host={os.environ["POSTGRES_HOST"]} '
        f'port={os.environ.get("POSTGRES_PORT", 5432)}'
    )


def _get_score_settings(db, group_id):
    cursor = db.cursor(cursor_factory=DictCursor)
    cursor.execute(
        'SELECT * FROM api_groupsettings WHERE group_id = %s LIMIT 1',
        (group_id, )
    )
    return cursor.fetchone()