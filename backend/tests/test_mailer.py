import os
import asyncio
from types import SimpleNamespace
from app.mailer import send_reset_email

class DummyResponse:
    def __init__(self, status_code=202):
        self.status_code = status_code
        self.body = b''

class DummySG:
    def __init__(self, *args, **kwargs):
        pass
    def send(self, message):
        # Basic assertion: message contains 'Reset your password' in subject or html
        assert message.subject == 'Reset your password'
        return DummyResponse(202)

def test_sendgrid_send(monkeypatch):
    # Ensure environment variable is set for the test
    monkeypatch.setenv('SENDGRID_API_KEY', 'test-key')
    # patch the client to our dummy
    monkeypatch.setattr('app.mailer.SendGridAPIClient', DummySG)

    token = 'test-token-123'
    # Run async function
    resp = asyncio.get_event_loop().run_until_complete(send_reset_email('user@example.com', token))
    assert resp.get('sent') is True

def test_dev_fallback(monkeypatch):
    # Ensure no SENDGRID key
    monkeypatch.delenv('SENDGRID_API_KEY', raising=False)
    token = 'test-token-456'
    resp = asyncio.get_event_loop().run_until_complete(send_reset_email('user@example.com', token))
    assert resp.get('sent') is False
    assert resp.get('token') == token
    assert 'preview_link' in resp
