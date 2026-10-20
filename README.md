# PyGuide

PyGuide is a full-stack Python learning assistant. It has a React user interface, a secure FastAPI backend, Neon PostgreSQL chat storage, and OpenRouter for AI answers. It is designed for learners: it explains Python concepts, helps with code, stores each user's private chats, and supports text-based file attachments.

> New to this project? Read [PROJECT_GUIDE.md](PROJECT_GUIDE.md). It is the complete beginner guide: every folder, how the app works, local setup, deployment, troubleshooting, and safe changes.

## What PyGuide includes

- Secure account registration, login, logout, and protected personal chat history.
- Responsive desktop, tablet, and mobile interface with a slide-out mobile sidebar.
- New chats, search, rename, archive, restore, and delete actions.
- Markdown and Python code formatting, copy actions, response regeneration, and message editing.
- Python-focused responses with existing knowledge-base fallbacks and OpenRouter integration.
- Safe file upload support for code and documents, plus attachment deletion and chat cleanup.
- Neon PostgreSQL persistence with per-user ownership checks.

## Project layout

```text
python-learning-assistant/
├── frontend/                  # React + Vite application (deploy to Vercel)
├── backend/                   # FastAPI API (deploy to Render)
├── chatbot.py                 # Python-question logic and OpenRouter client
├── config.py                  # Knowledge base and chatbot configuration
├── PROJECT_GUIDE.md           # Complete beginner documentation
├── .gitignore                 # Keeps secrets and generated files out of Git
└── README.md                  # This quick overview
```

## Quick local start (Windows PowerShell)

Open two terminals in the project folder.

### Terminal 1: backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `backend/.env` and add your real `DATABASE_URL`, `OPENROUTER_API_KEY`, and a long random `JWT_SECRET`. Then start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Check `http://localhost:8000/health`. It should return `{"status":"online"}`.

### Terminal 2: frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

For local use, `frontend/.env` must contain:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Deploy

| Service | What to deploy | Important setting |
| --- | --- | --- |
| Neon | Existing PostgreSQL database | `DATABASE_URL` belongs only on the backend. |
| Render | `backend/` FastAPI service | Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Vercel | `frontend/` Vite app | `VITE_API_BASE_URL=https://your-render-service.onrender.com` |

In Render, set `ALLOWED_ORIGINS` to your Vercel URL, for example `https://pyguide-five.vercel.app`. Never put the Neon URL, OpenRouter key, or JWT secret in Vercel.

## Security notes

- `.env` files, uploads, Python caches, frontend packages, and build output are ignored by Git.
- Passwords are hashed in the backend. Browser requests use a signed authentication token.
- Chats, messages, attachments, and settings are always scoped to the logged-in user.
- If a secret was ever pasted into chat, a screenshot, or a public commit, rotate it in Neon/OpenRouter/Render before deploying.

## Help

Use [PROJECT_GUIDE.md](PROJECT_GUIDE.md) for exact deployment steps, the database model, a troubleshooting table, and a manual test checklist.
