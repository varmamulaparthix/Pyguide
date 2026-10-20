"""FastAPI service for PyGuide."""
import os
import sys
import uuid
from io import BytesIO
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import psycopg
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
UPLOADS = ROOT / "backend" / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT))
# Support a backend-specific .env for local setup, while keeping deployment
# credentials in the host environment. The legacy root .env remains supported.
load_dotenv(ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from chatbot import get_response

DATABASE_URL = os.getenv("DATABASE_URL", "")
JWT_SECRET = os.getenv("JWT_SECRET", "")
if not DATABASE_URL or not JWT_SECRET:
    raise RuntimeError("DATABASE_URL and JWT_SECRET are required.")

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".py", ".txt", ".md", ".pdf", ".csv", ".json", ".log", ".png", ".jpg", ".jpeg", ".webp"}
TEXT_EXTENSIONS = {".py", ".txt", ".md", ".csv", ".json", ".log"}
app = FastAPI(title="PyGuide API", version="1.1")
origins = [value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if value.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()


def db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def token_for(user: dict) -> str:
    return jwt.encode({"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(days=7)}, JWT_SECRET, algorithm="HS256")


def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        user_id = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Your session has expired. Please log in again.") from exc
    with db() as connection:
        user = connection.execute("SELECT id, email FROM pyguide_users WHERE id=%s", (user_id,)).fetchone()
    if not user:
        raise HTTPException(401, "Your account could not be found. Please log in again.")
    return user


def require_chat(connection, chat_id: str, user_id):
    chat = connection.execute("SELECT * FROM pyguide_chats WHERE id=%s AND user_id=%s", (chat_id, user_id)).fetchone()
    if not chat:
        raise HTTPException(404, "Chat not found.")
    return chat


def extract_file_text(data: bytes, extension: str) -> str | None:
    """Extract only text that can safely be sent as user-provided chat context."""
    if extension in TEXT_EXTENSIONS:
        return data.decode("utf-8", errors="replace")[:12000]
    if extension == ".pdf":
        try:
            text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages)
            return text[:12000] or None
        except Exception:
            return None
    return None


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class Title(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class AskRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    attachment_ids: list[str] = Field(default_factory=list, max_length=8)


class ArchiveRequest(BaseModel):
    archived: bool


class EditMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)


@app.on_event("startup")
def initialise_database():
    statements = [
        "CREATE TABLE IF NOT EXISTS pyguide_users(id UUID PRIMARY KEY,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,created_at TIMESTAMPTZ DEFAULT now())",
        "CREATE TABLE IF NOT EXISTS pyguide_chats(id UUID PRIMARY KEY,user_id UUID NOT NULL REFERENCES pyguide_users(id) ON DELETE CASCADE,title TEXT NOT NULL,archived BOOLEAN NOT NULL DEFAULT false,created_at TIMESTAMPTZ DEFAULT now(),updated_at TIMESTAMPTZ DEFAULT now())",
        "CREATE TABLE IF NOT EXISTS pyguide_messages(id UUID PRIMARY KEY,chat_id UUID NOT NULL REFERENCES pyguide_chats(id) ON DELETE CASCADE,role TEXT NOT NULL CHECK(role IN ('user','assistant')),content TEXT NOT NULL,created_at TIMESTAMPTZ DEFAULT now())",
        "CREATE TABLE IF NOT EXISTS pyguide_attachments(id UUID PRIMARY KEY,user_id UUID NOT NULL REFERENCES pyguide_users(id) ON DELETE CASCADE,chat_id UUID REFERENCES pyguide_chats(id) ON DELETE SET NULL,original_name TEXT NOT NULL,stored_name TEXT NOT NULL,content_type TEXT,size_bytes INTEGER NOT NULL,text_content TEXT,created_at TIMESTAMPTZ DEFAULT now())",
        "CREATE TABLE IF NOT EXISTS pyguide_message_attachments(message_id UUID NOT NULL REFERENCES pyguide_messages(id) ON DELETE CASCADE,attachment_id UUID NOT NULL REFERENCES pyguide_attachments(id) ON DELETE CASCADE,PRIMARY KEY(message_id,attachment_id))",
        "CREATE INDEX IF NOT EXISTS pyguide_chats_user_idx ON pyguide_chats(user_id, updated_at DESC)",
        "CREATE INDEX IF NOT EXISTS pyguide_messages_chat_idx ON pyguide_messages(chat_id, created_at)",
        "CREATE INDEX IF NOT EXISTS pyguide_attachments_user_idx ON pyguide_attachments(user_id, created_at DESC)",
    ]
    with db() as connection:
        for statement in statements:
            connection.execute(statement)


@app.get("/health")
def health():
    try:
        with db() as connection:
            connection.execute("SELECT 1")
        return {"status": "online"}
    except Exception:
        return {"status": "offline"}


@app.post("/auth/register")
def register(payload: Credentials):
    email = payload.email.strip().lower()
    if "@" not in email or email.startswith("@"):
        raise HTTPException(422, "Enter a valid email address.")
    with db() as connection:
        if connection.execute("SELECT 1 FROM pyguide_users WHERE email=%s", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists.")
        user = {"id": uuid.uuid4(), "email": email}
        connection.execute("INSERT INTO pyguide_users(id,email,password_hash) VALUES(%s,%s,%s)", (user["id"], email, passwords.hash(payload.password)))
    return {"token": token_for(user), "user": user}


@app.post("/auth/login")
def login(payload: Credentials):
    with db() as connection:
        user = connection.execute("SELECT * FROM pyguide_users WHERE email=%s", (payload.email.strip().lower(),)).fetchone()
    if not user or not passwords.verify(payload.password, user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password.")
    return {"token": token_for(user), "user": {"id": user["id"], "email": user["email"]}}


@app.get("/chats")
def list_chats(q: str = "", archived: bool = False, user=Depends(current_user)):
    like = f"%{q.strip()}%"
    with db() as connection:
        return connection.execute(
            """SELECT c.* FROM pyguide_chats c WHERE c.user_id=%s AND c.archived=%s AND
            (c.title ILIKE %s OR EXISTS (SELECT 1 FROM pyguide_messages m WHERE m.chat_id=c.id AND m.content ILIKE %s))
            ORDER BY c.updated_at DESC""",
            (user["id"], archived, like, like),
        ).fetchall()


@app.post("/chats")
def create_chat(payload: Title, user=Depends(current_user)):
    chat = {"id": uuid.uuid4(), "title": payload.title.strip()}
    with db() as connection:
        connection.execute("INSERT INTO pyguide_chats(id,user_id,title) VALUES(%s,%s,%s)", (chat["id"], user["id"], chat["title"]))
    return chat


@app.get("/chats/{chat_id}/messages")
def chat_messages(chat_id: str, user=Depends(current_user)):
    with db() as connection:
        require_chat(connection, chat_id, user["id"])
        return connection.execute(
            """SELECT m.*, COALESCE(array_agg(a.original_name) FILTER (WHERE a.id IS NOT NULL), '{}') AS attachment_names
            FROM pyguide_messages m
            LEFT JOIN pyguide_message_attachments ma ON ma.message_id=m.id
            LEFT JOIN pyguide_attachments a ON a.id=ma.attachment_id
            WHERE m.chat_id=%s GROUP BY m.id ORDER BY m.created_at""", (chat_id,)
        ).fetchall()


@app.patch("/chats/{chat_id}")
def rename_chat(chat_id: str, payload: Title, user=Depends(current_user)):
    with db() as connection:
        updated = connection.execute("UPDATE pyguide_chats SET title=%s,updated_at=now() WHERE id=%s AND user_id=%s RETURNING id", (payload.title.strip(), chat_id, user["id"])).fetchone()
    if not updated:
        raise HTTPException(404, "Chat not found.")
    return {"ok": True}


@app.patch("/chats/{chat_id}/archive")
def archive_chat(chat_id: str, payload: ArchiveRequest, user=Depends(current_user)):
    with db() as connection:
        updated = connection.execute("UPDATE pyguide_chats SET archived=%s,updated_at=now() WHERE id=%s AND user_id=%s RETURNING id", (payload.archived, chat_id, user["id"])).fetchone()
    if not updated:
        raise HTTPException(404, "Chat not found.")
    return {"ok": True}


@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: str, user=Depends(current_user)):
    stored_files = []
    with db() as connection:
        require_chat(connection, chat_id, user["id"])
        stored_files = connection.execute("SELECT stored_name FROM pyguide_attachments WHERE user_id=%s AND chat_id=%s", (user["id"], chat_id)).fetchall()
        connection.execute("DELETE FROM pyguide_attachments WHERE user_id=%s AND chat_id=%s", (user["id"], chat_id))
        deleted = connection.execute("DELETE FROM pyguide_chats WHERE id=%s AND user_id=%s RETURNING id", (chat_id, user["id"])).fetchone()
    if not deleted:
        raise HTTPException(404, "Chat not found.")
    for stored_file in stored_files:
        path = UPLOADS / str(user["id"]) / stored_file["stored_name"]
        if path.exists():
            path.unlink()
    return {"ok": True}


@app.post("/messages/{message_id}/edit-and-ask")
def edit_and_regenerate(message_id: str, payload: EditMessageRequest, user=Depends(current_user)):
    """Replace a user message and discard its obsolete response branch."""
    content = payload.content.strip()
    with db() as connection:
        message = connection.execute(
            """SELECT m.*, c.user_id FROM pyguide_messages m
            JOIN pyguide_chats c ON c.id=m.chat_id
            WHERE m.id=%s AND c.user_id=%s""", (message_id, user["id"])
        ).fetchone()
        if not message or message["role"] != "user":
            raise HTTPException(404, "The message could not be edited.")
        history = connection.execute(
            "SELECT role,content FROM pyguide_messages WHERE chat_id=%s AND created_at < %s ORDER BY created_at DESC LIMIT 8",
            (message["chat_id"], message["created_at"]),
        ).fetchall()[::-1]
        connection.execute("UPDATE pyguide_messages SET content=%s WHERE id=%s", (content, message_id))
        connection.execute("DELETE FROM pyguide_messages WHERE chat_id=%s AND created_at > %s", (message["chat_id"], message["created_at"]))
    try:
        answer = get_response(content, history=history)
    except Exception as exc:
        raise HTTPException(503, "The AI service is unavailable right now. Please try again shortly.") from exc
    assistant_id = uuid.uuid4()
    with db() as connection:
        connection.execute("INSERT INTO pyguide_messages(id,chat_id,role,content) VALUES(%s,%s,'assistant',%s)", (assistant_id, message["chat_id"], answer))
        connection.execute("UPDATE pyguide_chats SET updated_at=now() WHERE id=%s", (message["chat_id"],))
    return {"content": answer, "assistant_message_id": assistant_id}


@app.post("/attachments")
async def upload_attachments(files: list[UploadFile] = File(...), user=Depends(current_user)):
    if len(files) > 8:
        raise HTTPException(422, "Attach no more than 8 files at once.")
    uploaded = []
    for upload in files:
        original_name = Path(upload.filename or "attachment").name
        extension = Path(original_name).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(415, f"{original_name}: this file type is not supported.")
        data = await upload.read(MAX_FILE_SIZE + 1)
        if not data:
            raise HTTPException(422, f"{original_name}: the file is empty.")
        if len(data) > MAX_FILE_SIZE:
            raise HTTPException(413, f"{original_name}: files must be 5 MB or smaller.")
        attachment_id = uuid.uuid4()
        stored_name = f"{attachment_id}{extension}"
        folder = UPLOADS / str(user["id"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / stored_name).write_bytes(data)
        text_content = extract_file_text(data, extension)
        record = {"id": attachment_id, "name": original_name, "type": upload.content_type or "application/octet-stream", "size": len(data)}
        with db() as connection:
            connection.execute("INSERT INTO pyguide_attachments(id,user_id,original_name,stored_name,content_type,size_bytes,text_content) VALUES(%s,%s,%s,%s,%s,%s,%s)", (attachment_id, user["id"], original_name, stored_name, record["type"], record["size"], text_content))
        uploaded.append(record)
    return uploaded


@app.get("/attachments")
def list_attachments(user=Depends(current_user)):
    with db() as connection:
        return connection.execute("SELECT id,original_name AS name,content_type AS type,size_bytes AS size,created_at,chat_id FROM pyguide_attachments WHERE user_id=%s ORDER BY created_at DESC", (user["id"],)).fetchall()


@app.get("/attachments/{attachment_id}/download")
def download_attachment(attachment_id: str, user=Depends(current_user)):
    with db() as connection:
        attachment = connection.execute("SELECT * FROM pyguide_attachments WHERE id=%s AND user_id=%s", (attachment_id, user["id"])).fetchone()
    if not attachment:
        raise HTTPException(404, "File not found.")
    path = UPLOADS / str(user["id"]) / attachment["stored_name"]
    if not path.is_file():
        raise HTTPException(404, "The stored file is no longer available.")
    return FileResponse(path, media_type=attachment["content_type"], filename=attachment["original_name"])


@app.delete("/attachments/{attachment_id}")
def delete_attachment(attachment_id: str, user=Depends(current_user)):
    with db() as connection:
        attachment = connection.execute("DELETE FROM pyguide_attachments WHERE id=%s AND user_id=%s RETURNING stored_name", (attachment_id, user["id"])).fetchone()
    if not attachment:
        raise HTTPException(404, "File not found.")
    path = UPLOADS / str(user["id"]) / attachment["stored_name"]
    if path.exists():
        path.unlink()
    return {"ok": True}


@app.post("/chats/{chat_id}/ask")
def ask(chat_id: str, payload: AskRequest, user=Depends(current_user)):
    content = payload.content.strip()
    if not content:
        raise HTTPException(422, "Write a Python question before sending.")
    with db() as connection:
        chat = require_chat(connection, chat_id, user["id"])
        history = connection.execute("SELECT role,content FROM pyguide_messages WHERE chat_id=%s ORDER BY created_at DESC LIMIT 8", (chat_id,)).fetchall()[::-1]
        attachments = []
        for attachment_id in payload.attachment_ids:
            attachment = connection.execute("SELECT * FROM pyguide_attachments WHERE id=%s AND user_id=%s", (attachment_id, user["id"])).fetchone()
            if not attachment:
                raise HTTPException(404, "One selected attachment was not found.")
            attachments.append(attachment)
        unreadable_pdfs = [item["original_name"] for item in attachments if Path(item["original_name"]).suffix.lower() == ".pdf" and not item["text_content"]]
        if unreadable_pdfs:
            raise HTTPException(422, f"PyGuide could not extract readable text from {', '.join(unreadable_pdfs)}. It may be a scanned PDF; upload a text-based PDF or paste the relevant text.")
        image_names = [item["original_name"] for item in attachments if Path(item["original_name"]).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        if image_names:
            raise HTTPException(422, "Image understanding is not configured for this model. Describe the image, or upload a Python, text, or text-based PDF file for analysis.")
        message_id = uuid.uuid4()
        connection.execute("INSERT INTO pyguide_messages(id,chat_id,role,content) VALUES(%s,%s,'user',%s)", (message_id, chat_id, content))
        for attachment in attachments:
            connection.execute("UPDATE pyguide_attachments SET chat_id=%s WHERE id=%s", (chat_id, attachment["id"]))
            connection.execute("INSERT INTO pyguide_message_attachments(message_id,attachment_id) VALUES(%s,%s) ON CONFLICT DO NOTHING", (message_id, attachment["id"]))
        if chat["title"] == "New chat":
            connection.execute("UPDATE pyguide_chats SET title=%s WHERE id=%s", (content[:48], chat_id))
    file_context = "\n\n".join(f"Attached file {item['original_name']}:\n{item['text_content']}" for item in attachments if item["text_content"])
    try:
        answer = get_response(content + (f"\n\n{file_context}" if file_context else ""), history=history)
    except Exception as exc:
        raise HTTPException(503, "The AI service is unavailable right now. Please try again shortly.") from exc
    assistant_id = uuid.uuid4()
    with db() as connection:
        connection.execute("INSERT INTO pyguide_messages(id,chat_id,role,content) VALUES(%s,%s,'assistant',%s)", (assistant_id, chat_id, answer))
        connection.execute("UPDATE pyguide_chats SET updated_at=now() WHERE id=%s", (chat_id,))
    return {"content": answer, "user_message_id": message_id, "assistant_message_id": assistant_id}
