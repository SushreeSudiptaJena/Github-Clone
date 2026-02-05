async def send_reset_email(to_email: str, token: str) -> dict:
    """Email support has been removed; calling this will raise an error."""
    raise RuntimeError("Email support is disabled in this deployment. No emails can be sent.")
