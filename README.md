# PyGuide

PyGuide is a full-stack Python learning chatbot. The frontend is React + Vite for Vercel; the secure backend is FastAPI for Render; chat data is stored in Neon PostgreSQL.

## Structure

```text
frontend/        React + Vite UI
backend/         FastAPI API, authentication, Neon persistence
chatbot.py       Existing Python-aware AI logic reused by the backend
config.py        Existing learning knowledge base and OpenRouter settings
```

## Local run

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Copy `backend/.env.example` to `backend/.env`, then set `DATABASE_URL`, `OPENROUTER_API_KEY`, and a long random `JWT_SECRET`.

The backend also reads the existing root `.env` for backward compatibility. Never commit either `.env` file.

```powershell
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Then run:

```powershell
npm run dev
```

## Deployment

### Render backend

1. Create a Render Web Service from this repository.
2. Root directory: `backend`.
3. Build command: `pip install -r requirements.txt`.
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Add environment variables: `DATABASE_URL`, `OPENROUTER_API_KEY`, `JWT_SECRET`, and `ALLOWED_ORIGINS=https://your-vercel-app.vercel.app`.

### Vercel frontend

1. Import the repository in Vercel.
2. Root directory: `frontend`.
3. Add `VITE_API_BASE_URL=https://your-render-service.onrender.com`.
4. Deploy. Do not add database or OpenRouter secrets to Vercel.

## Security

The browser never receives the Neon or OpenRouter credentials. Passwords are hashed, chat endpoints require a signed JWT, and every chat query is scoped to the authenticated user.

## Attachments

Use the **+** button beside the composer and select an item from its menu. PyGuide accepts up to eight files, 5 MB each: Python, text, Markdown, CSV, JSON, log, and text-based PDF files. Python/text/PDF content is safely extracted and sent as context only for the message that includes it. Uploaded files can be opened from **Files**, downloaded, or permanently deleted through each file's three-dot menu.

Image files can be stored and downloaded, but image understanding is deliberately not claimed because the configured text model does not provide it. Scanned PDFs likewise need OCR, which is not configured.
