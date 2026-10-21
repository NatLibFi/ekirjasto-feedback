import pytest
from flask import url_for
from app import app as flask_app
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
import municipalities

@pytest.fixture
def client(monkeypatch):
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost'
    flask_app.config['APPLICATION_ROOT'] = '/'
    flask_app.config['PREFERRED_URL_SCHEME'] = 'http'
    flask_app.config['FEEDBACK_MUNICIPALITIES_URL'] = 'http://circulation.test/internal/feedback/municipalities'
    flask_app.config['FEEDBACK_SERVICE_TOKEN'] = 'test-service-token'
    municipalities._municipalities_cache = None
    municipalities._cache_expires_at = 0.0
    response = MagicMock()
    response.json.return_value = {
        'municipalities': [
            {'code': '001', 'name': 'Test City', 'email': 'city@example.fi'},
            {'code': '002', 'name': 'Sample Town', 'email': 'team@example.fi'},
        ]
    }
    response.raise_for_status.return_value = None
    monkeypatch.setattr(municipalities.httpx, 'get', lambda *args, **kwargs: response)
    with flask_app.test_client() as client:
        yield client

def test_feedback_honeypot_prevents_message_send(client):
    """Test that filling the honeypot field prevents the message from being sent."""
    with flask_app.app_context():
        response = client.get(url_for('feedback'))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

        data = {
            'subject': 'Yleinen palaute',
            'book_name':'Testikirja',
            'message': 'Testiviesti',
            'municipality': '001',
            'email': '',
            'hp_field': 'To bot or not to bot',  # Bot leaves us a nice message
            'csrf_token': csrf_token,
            'submit': 'Send',
        }
        post_response = client.post(url_for('feedback'), data=data, follow_redirects=True)
        assert post_response.status_code == 400
        assert b'Bot detected' in post_response.data

def test_feedback_empty_honeypot_allows_message_send(client):
    """Test that leaving the honeypot field empty allows the message to be sent."""
    with flask_app.app_context():
        response = client.get(url_for('feedback'))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

        data = {
            'subject': 'Yleinen palaute',
            'book_name': 'Testikirja',
            'message': 'Testiviesti',
            'municipality': '001',
            'email': '',
            'hp_field': '',  # Human leaves honeypot empty
            'csrf_token': csrf_token,
            'submit': 'Send',
            'device_manufacturer': 'Test Manufacturer',
            'device_model': 'Test Model',
            'version_name': '1.0',
            'version_code': '1',
            'commit': 'abc123',
        }
        with patch('smtplib.SMTP') as smtp:
            post_response = client.post(url_for('feedback'), data=data, follow_redirects=True)
            assert post_response.status_code == 200
            assert b'Kiitos palautteesta!' in post_response.data
            recipients = smtp.return_value.__enter__.return_value.sendmail.call_args.args[1]
            assert 'city@example.fi' in recipients

def test_feedback_invalid_municipality_renders_form(client):
    """Test that selecting an invalid municipality re-renders the form."""
    with flask_app.app_context():
        response = client.get(url_for('feedback'))
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

        data = {
            'subject': 'Yleinen palaute',
            'book_name': 'Testikirja',
            'message': 'Testiviesti',
            'municipality': '9999',  # Invalid value
            'email': '',
            'hp_field': '',
            'csrf_token': csrf_token,
            'submit': 'Send',
            'device_manufacturer': 'Test Manufacturer',
            'device_model': 'Test Model',
            'version_name': '1.0',
            'version_code': '1',
            'commit': 'abc123',
        }
        with patch('smtplib.SMTP', MagicMock()):
            post_response = client.post(url_for('feedback'), data=data, follow_redirects=True)
            # Should show an error message or re-render the form with errors
            assert post_response.status_code == 200
