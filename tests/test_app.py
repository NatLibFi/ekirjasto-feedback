import pytest
from flask import url_for
from app import app as flask_app
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    flask_app.config['SERVER_NAME'] = 'localhost'
    flask_app.config['APPLICATION_ROOT'] = '/'
    flask_app.config['PREFERRED_URL_SCHEME'] = 'http'
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
            'municipality': '1',
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
            'municipality': 1,
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
        with patch('smtplib.SMTP', MagicMock()):
            post_response = client.post(url_for('feedback'), data=data, follow_redirects=True)
            assert post_response.status_code == 200
            assert b'Kiitos palautteesta!' in post_response.data

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
            'municipality': 9999,  # Invalid value
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
