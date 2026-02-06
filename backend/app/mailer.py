import os
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def _build_reset_link(*, reset_link: Optional[str], token: Optional[str]) -> Optional[str]:
    if reset_link:
        return reset_link

    if not token:
        return None

    frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
    if not frontend_url:
        return None

    # common reset route; adjust if your frontend uses a different path
    return f"{frontend_url}/reset-password?token={token}"


def send_reset_email(*args: Any, **kwargs: Any) -> bool:
    """
    Send a password reset email.

    This function is intentionally tolerant about parameters so it won't break
    if call sites vary. Supported inputs:
      - send_reset_email(email, token)
      - send_reset_email(email, reset_link)
      - send_reset_email(to_email=..., token=...)
      - send_reset_email(to_email=..., reset_link=...)

    Env vars:
      - SENDGRID_API_KEY (if missing -> no-op)
      - SENDGRID_FROM_EMAIL (default: no-op if missing)
      - FRONTEND_URL (used to build link from token)
    """
    # Try to extract email + token/link from args/kwargs
    to_email = (
        kwargs.get("to_email")
        or kwargs.get("email")
        or kwargs.get("recipient")
        or (args[0] if len(args) >= 1 else None)
    )

    second = args[1] if len(args) >= 2 else None
    token = kwargs.get("token") or (second if isinstance(second, str) and len(second) < 300 else None)
    reset_link = kwargs.get("reset_link") or kwargs.get("reset_url") or kwargs.get("link")
    if reset_link is None and isinstance(second, str) and second and second.startswith(("http://", "https://")):
        reset_link = second

    reset_link = _build_reset_link(reset_link=reset_link, token=token)

    if not to_email or not isinstance(to_email, str):
        logger.warning("send_reset_email: missing to_email; skipping email send")
        return False

    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")

    # If not configured, don't crash production deploys—just no-op.
    if not api_key or not from_email:
        logger.info(
            "send_reset_email: SendGrid not configured (missing SENDGRID_API_KEY or SENDGRID_FROM_EMAIL); skipping"
        )
        return False

    if not reset_link:
        logger.warning("send_reset_email: missing reset link/token (and FRONTEND_URL not set); skipping")
        return False

    subject = kwargs.get("subject") or "Reset your password"
    html_content = f"""
    <p>You requested a password reset.</p>
    <p><a href="{reset_link}">Click here to reset your password</a></p>
    <p>If you didn’t request this, you can ignore this email.</p>
    """.strip()

    try:
        # Import lazily so missing dependency doesn't crash app boot.
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content,
        )
        sg = SendGridAPIClient(api_key)
        resp = sg.send(message)
        logger.info("send_reset_email: sent to=%s status=%s", to_email, getattr(resp, "status_code", None))
        return True
    except ModuleNotFoundError:
        logger.info("send_reset_email: sendgrid package not installed; skipping")
        return False
    except Exception:
        logger.exception("send_reset_email: failed to send email")
        return False
