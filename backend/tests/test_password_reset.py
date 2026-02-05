from httpx import AsyncClient
from app.main import app

async def test_password_reset_disabled():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        # register
        r = await ac.post('/api/register', json={'username':'resetuser','password':'bigpass123'})
        assert r.status_code == 200
        # request reset should be disabled (410)
        r2 = await ac.post('/api/request-password-reset', json={'username':'resetuser'})
        assert r2.status_code == 410
        # reset endpoint also disabled
        r3 = await ac.post('/api/reset-password', json={'token':'dummy','new_password':'newpass456'})
        assert r3.status_code == 410
