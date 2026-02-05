import pytest
import asyncio
from app.mailer import send_reset_email

def test_email_support_disabled():
    token = 'test-token-123'
    with pytest.raises(RuntimeError):
        asyncio.get_event_loop().run_until_complete(send_reset_email('user@example.com', token))
