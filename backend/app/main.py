import os
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from .db import init_db, get_session
from .openai_adapter import call_chat, stream_chat
from sqlmodel import select
from .models import Message, Session
from .crud import create_session, get_sessions, get_session, create_message, get_messages, get_session_by_name, get_user_by_email
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

# Monitoring and rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
import os

app = FastAPI(title="Gemini-Clone API")

# Application environment
APP_ENV = os.getenv('APP_ENV', 'development')

# Rate limiter (use Redis in production by setting up a Redis URL)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    prompt: str
    session_id: int | None = None
    session_name: str = "default"

class SessionCreate(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/api/health")
async def health():
    return {"status":"ok"}

# Auth endpoints
from .auth import get_password_hash, verify_password, create_access_token, get_current_user_header, get_user_from_token
from .mailer import send_reset_email

@limiter.limit("5/minute")
@app.post("/api/register")
async def register(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    # validation
    if len(payload.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    existing = await get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    if payload.email:
        existing_email = await get_user_by_email(db, payload.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already in use")
    hashed = get_password_hash(payload.password)
    user = await create_user(db, payload.username, hashed, payload.email)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type":"bearer", "user": {"id": user.id, "username": user.username, "email": user.email}}

@limiter.limit("10/minute")
@app.post("/api/login")
async def login(payload: UserCreate, db: AsyncSession = Depends(get_session)):
    user = await get_user_by_username(db, payload.username)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type":"bearer", "user": {"id": user.id, "username": user.username, "email": user.email}}

class PasswordResetRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

@app.post('/api/request-password-reset')
@limiter.limit("5/minute")
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_session)):
    user = None
    if payload.email:
        user = await get_user_by_email(db, payload.email)
    elif payload.username:
        user = await get_user_by_username(db, payload.username)

    # Always return success to avoid username/email enumeration
    if not user:
        return {"ok": True, "message": "If the user exists, a reset token has been issued (in production emailed)."}

    token = create_password_reset_token(user.username)
    # Send email if possible
    result = await send_reset_email(user.email, token) if user.email else {'sent': False, 'message': 'No email configured for user'}
    if result.get('sent'):
        return {"ok": True, "message": "Reset token sent to your email."}
    # Fallback for dev: include token/preview link in response only when not production
    if os.getenv('APP_ENV', 'development') != 'production':
        return {"ok": True, "reset_token": result.get('token'), "preview_link": result.get('preview_link'), "message": result.get('error') or 'Email not configured or failed; returning token for dev.'}
    return {"ok": True, "message": "If the user exists, a reset token has been issued (in production it is emailed)."}

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@app.post('/api/request-password-reset')
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_session)):
    user = await get_user_by_username(db, payload.username)
    # Always return success to avoid username enumeration
    if not user:
        return {"ok": True, "message": "If the user exists, a reset token has been issued (in production emailed)."}
    token = create_password_reset_token(user.username)
    # In production send email; here we return the token for developer convenience
    return {"ok": True, "reset_token": token}

@app.post('/api/reset-password')
async def reset_password(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_session)):
    username = verify_password_reset_token(payload.token)
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = await get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed = get_password_hash(payload.new_password)
    await update_user_password(db, user.id, hashed)
    return {"ok": True, "message": "Password reset successful"}

@app.post('/api/change-password')
async def change_password(data: PasswordResetConfirm, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_header)):
    # reuse PasswordResetConfirm model but token field will be used as old_password
    old_password = data.token
    new_password = data.new_password
    if not verify_password(old_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Old password is incorrect")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    hashed = get_password_hash(new_password)
    await update_user_password(db, current_user.id, hashed)
    return {"ok": True, "message": "Password changed"}

@app.post("/api/sessions")
async def api_create_session(payload: SessionCreate, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    existing = await get_session_by_name(db, payload.name, current_user.id)
    if existing:
        return existing
    s = await create_session(db, payload.name, user_id=current_user.id)
    return s

@app.get("/api/sessions")
async def api_get_sessions(db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    return await get_sessions(db, current_user.id)

@app.get("/api/sessions/{session_id}/messages")
async def api_get_messages(session_id: int, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user)):
    s = await get_session(db, session_id)
    if not s or s.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return await get_messages(db, session_id)

@app.post("/api/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_session), current_user=Depends(get_current_user_header)):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt required")
    # find or create session (scoped to user)
    session_obj = None
    if req.session_id:
        session_obj = await get_session(db, req.session_id)
    if not session_obj:
        session_obj = await get_session_by_name(db, req.session_name, current_user.id)
    if not session_obj:
        session_obj = await create_session(db, req.session_name, user_id=current_user.id)

    # persist user message
    await create_message(db, session_obj.id, 'user', req.prompt)

    # get model answer
    answer = await call_chat(req.prompt)

    # persist assistant message
    await create_message(db, session_obj.id, 'assistant', answer)

    return {"answer": answer, "session_id": session_obj.id}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        prompt = data.get('prompt')
        session_id = data.get('session_id')
        session_name = data.get('session_name', 'default')
        token = data.get('token')

        # get db session via dependency emulation and validate token
        async for db in get_session():
            user = None
            if token:
                user = await get_user_from_token(token, db)

            # find or create session scoped to user
            session_obj = None
            if session_id:
                session_obj = await get_session(db, session_id)
            if not session_obj:
                session_obj = await get_session_by_name(db, session_name, user.id if user else None)
            if not session_obj:
                session_obj = await create_session(db, session_name, user_id=user.id if user else None)

            # persist user message
            await create_message(db, session_obj.id, 'user', prompt)

            # buffer assistant response while streaming
            buffer = ''
            async for chunk in stream_chat(prompt):
                buffer += chunk
                await websocket.send_json({"type":"chunk","text":chunk})

            # save assistant message once streaming finished
            await create_message(db, session_obj.id, 'assistant', buffer)
            await websocket.send_json({"type":"done","session_id": session_obj.id})
            break

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type":"error", "detail": str(e)})
        await websocket.close()
