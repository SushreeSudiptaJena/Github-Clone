import os
import asyncio
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
OUTBOX_DIR = os.path.join(BASE_DIR, '..', 'outbox')

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@example.com')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Setup Jinja environment
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

os.makedirs(OUTBOX_DIR, exist_ok=True)

async def send_reset_email(to_email: str, token: str) -> dict:
    """Send password reset email using Jinja templates.
    If SENDGRID_API_KEY is not configured, email is written to `backend/outbox/` and returned as preview info.
    """
    reset_link = f"{FRONTEND_URL}/?reset_token={token}"

    # Render templates if available
    plain_text = f"Reset your password by visiting: {reset_link}\nOr use this token: {token}"
    html_content = f"<p>Reset your password: <a href=\"{reset_link}\">Reset link</a></p><pre>{token}</pre>"
    try:
        txt_t = jinja_env.get_template('reset_email.txt')
        html_t = jinja_env.get_template('reset_email.html')
        plain_text = txt_t.render(reset_link=reset_link, token=token)
        html_content = html_t.render(reset_link=reset_link, token=token)
    except Exception:
        # Templates optional; fall back to simple messages
        pass

    # If no SendGrid configured, write to outbox for manual retrieval
    if not SENDGRID_API_KEY:
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        safe_email = to_email.replace('@', '_at_')
        base_name = f"reset_{safe_email}_{ts}"
        txt_path = os.path.join(OUTBOX_DIR, base_name + '.txt')
        html_path = os.path.join(OUTBOX_DIR, base_name + '.html')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(plain_text)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return {'sent': False, 'outbox': {'txt': txt_path, 'html': html_path}, 'token': token, 'preview_link': reset_link}

    # Lazy import SendGrid only when needed (keeps library optional)
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
    except Exception:
        return {'sent': False, 'error': 'SendGrid library not installed'}

    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=to_email,
        subject='Reset your password',
        plain_text_content=plain_text,
        html_content=html_content
    )

    loop = asyncio.get_event_loop()
    def _send():
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(message)
        return resp

    try:
        resp = await loop.run_in_executor(None, _send)
        if resp.status_code in (200, 202):
            return {'sent': True}
        else:
            return {'sent': False, 'error': resp.body}
    except Exception as e:
        return {'sent': False, 'error': str(e)}
