from httpx import AsyncClient
from app.main import app

async def test_password_reset_flow():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        # register
        r = await ac.post('/api/register', json={'username':'resetuser','password':'bigpass123'})
        assert r.status_code == 200
        # request reset
        r2 = await ac.post('/api/request-password-reset', json={'username':'resetuser'})
        assert r2.status_code == 200
        body = r2.json()
        assert body.get('ok') is True
        token = body.get('reset_token')
        assert token
        # perform reset
        r3 = await ac.post('/api/reset-password', json={'token': token, 'new_password':'newpass456'})
        assert r3.status_code == 200
        # login with new password
        r4 = await ac.post('/api/login', json={'username':'resetuser','password':'newpass456'})
        assert r4.status_code == 200
        assert r4.json().get('access_token')
