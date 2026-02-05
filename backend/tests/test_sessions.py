import asyncio
from httpx import AsyncClient
from app.main import app

async def test_sessions_workflow():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        # register and login
        r = await ac.post('/api/register', json={'username':'tester','password':'pass123'})
        assert r.status_code == 200
        token = r.json()['access_token']

        headers = {'Authorization': f'Bearer {token}'}

        # create session
        r = await ac.post('/api/sessions', json={'name':'test-session'}, headers=headers)
        assert r.status_code == 200
        s = r.json()
        assert s['name'] == 'test-session'

        # get sessions
        r2 = await ac.get('/api/sessions', headers=headers)
        assert r2.status_code == 200
        sessions = r2.json()
        assert any(x['name']=='test-session' for x in sessions)

        # post chat
        r3 = await ac.post('/api/chat', json={'prompt':'hi there','session_id': s['id']}, headers=headers)
        assert r3.status_code == 200
        resp = r3.json()
        assert 'answer' in resp

        # get messages
        r4 = await ac.get(f"/api/sessions/{s['id']}/messages", headers=headers)
        assert r4.status_code == 200
        msgs = r4.json()
        assert any(m['role']=='user' and 'hi there' in m['content'] for m in msgs)
