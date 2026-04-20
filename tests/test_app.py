import pytest
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'


def test_shorten_missing_url(client):
    response = client.post(
        '/shorten',
        content_type='application/json',
        data=json.dumps({})
    )
    assert response.status_code == 400


def test_shorten_valid_url(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    with patch('app.get_db', return_value=mock_conn):
        response = client.post(
            '/shorten',
            content_type='application/json',
            data=json.dumps({"url": "https://google.com"})
        )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'short_url' in data
    assert 'code' in data
    assert len(data['code']) == 6


def test_redirect_invalid_code(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = None
    mock_conn.cursor.return_value = mock_cur

    with patch('app.get_db', return_value=mock_conn):
        response = client.get('/invalidcode123')
    assert response.status_code == 404


def test_redirect_valid_code(client):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = ("https://google.com",)
    mock_conn.cursor.return_value = mock_cur

    with patch('app.get_db', return_value=mock_conn):
        response = client.get('/abc123')
    assert response.status_code == 302