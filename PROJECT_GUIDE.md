# PyGuide: Complete Beginner Project Guide

This is the handover guide for PyGuide. It is written for a person who has never used React, FastAPI, Git, Neon, Render, or Vercel before. Read it from top to bottom the first time. Later, use the table of contents to jump to the part you need.

## Contents

1. [What PyGuide is](#1-what-pyguide-is)
2. [How the pieces connect](#2-how-the-pieces-connect)
3. [Folder and file map](#3-folder-and-file-map)
4. [What each important file does](#4-what-each-important-file-does)
5. [Requirements before you start](#5-requirements-before-you-start)
6. [Environment variables and secrets](#6-environment-variables-and-secrets)
7. [Run the project locally](#7-run-the-project-locally)
8. [Use the application](#8-use-the-application)
9. [Database and user privacy](#9-database-and-user-privacy)
10. [Files and attachments](#10-files-and-attachments)
11. [Deploy to Neon, Render, and Vercel](#11-deploy-to-neon-render-and-vercel)
12. [Test before sharing](#12-test-before-sharing)
13. [Troubleshooting](#13-troubleshooting)
14. [Safe future changes](#14-safe-future-changes)
15. [Git basics](#15-git-basics)

---

## 1. What PyGuide is

PyGuide is a **Python learning chatbot**. A user creates an account, starts a chat, asks a Python question, and receives a beginner-friendly response. The user can return later and see the same chats because they are stored in a database.

The project has two applications:

- **Frontend**: what the user sees in the browser. It is built with React, TypeScript, and Vite.
- **Backend**: the protected server application. It is built with Python and FastAPI. It verifies users, stores data, uploads files, and calls OpenRouter.

The browser never receives the database password or OpenRouter API key. This separation is important for security.

## 2. How the pieces connect

```text
Browser (React on Vercel)
        |
        | HTTPS requests with the user's login token
        v
FastAPI backend (Render)
        |------------------> Neon PostgreSQL (users, chats, messages, files)
        |
        |------------------> OpenRouter (AI answer)
        v
Response shown in the chat UI
```

Example: when someone asks “Explain Python lists”:

1. React sends the text and the signed-in user's token to FastAPI.
2. FastAPI checks the token and confirms which user made the request.
3. FastAPI saves the user message in Neon.
4. The existing chatbot logic checks whether the request is about Python and can use its knowledge base.
5. If needed, the backend securely asks OpenRouter for an answer.
6. FastAPI saves the assistant response in Neon and returns it to React.
7. React displays the answer and keeps it in that chat history.

## 3. Folder and file map

```text
python-learning-assistant/
│
├── frontend/                         Browser application; deploy this to Vercel
│   ├── src/
│   │   ├── main.tsx                  React UI, state, API calls, user actions
│   │   ├── style.css                 All colors, layout, desktop and mobile styles
│   │   └── vite-env.d.ts             TypeScript support supplied by Vite
│   ├── index.html                    The one HTML page that starts React
│   ├── package.json                  Frontend packages and npm commands
│   ├── package-lock.json             Exact locked package versions
│   ├── tsconfig.json                 TypeScript rules
│   └── .env.example                  Safe frontend environment variable example
│
├── backend/                          Secure server; deploy this to Render
│   ├── app/
│   │   ├── __init__.py               Marks app as a Python package
│   │   └── main.py                   FastAPI routes, auth, database, uploads
│   ├── uploads/                      Temporary local uploaded files; ignored by Git
│   ├── requirements.txt              Backend Python packages
│   └── .env.example                  Safe backend environment variable example
│
├── chatbot.py                        Python-focused AI and OpenRouter logic
├── config.py                         Knowledge base, prompts, topic configuration
├── README.md                         Short project overview and quick start
├── PROJECT_GUIDE.md                  This complete guide
├── .gitignore                        Files Git must never upload
└── .env                              Local secret values only; ignored by Git
```

Generated folders such as `frontend/node_modules`, `frontend/dist`, `.venv`, `__pycache__`, and `backend/uploads` are not source code. They are created on your computer while installing, building, or uploading. They are intentionally ignored by Git.

## 4. What each important file does

### `frontend/src/main.tsx`

This is the main browser code. It contains the React components and state that make the screen interactive.

It is responsible for:

- Showing login and account creation forms.
- Keeping the login token only in browser storage for the signed-in session.
- Calling backend API endpoints such as `/auth/login`, `/chats`, `/uploads`, and `/health`.
- Rendering the sidebar, search field, recent chats, message list, settings window, files window, and composer.
- Opening and closing the mobile sidebar drawer.
- Creating a chat only when the first real message is sent. Clicking **New chat** only clears the screen; it does not create empty duplicate chats.
- Editing a previous message and asking the backend to remove obsolete replies and generate a new answer.
- Showing user-friendly errors when the backend is offline, slow, or rejects a request.

### `frontend/src/style.css`

This is the complete visual design. It has normal desktop styles first and clear responsive rules below them.

The important mobile behavior is in `@media (max-width: 1024px)` and `@media (max-width: 420px)`:

- The sidebar becomes a slide-out drawer instead of taking permanent screen space.
- The drawer is up to 340px wide or 88% of the phone width.
- Chat messages use 16px text and nearly the full available phone width.
- Composer buttons are 48 × 48px, suitable for touch.
- Login inputs and buttons are 52px high and use 16px text.
- The attachment menu becomes a wide, easy-to-tap mobile popover.

Do not use browser zoom or CSS `transform: scale()` to change mobile size. Change these responsive rules instead.

### `frontend/index.html`

Vite serves this small HTML file. It has one element called `root`. React mounts the whole interface inside that element. Most visible UI is **not** written in this file; it is written in `main.tsx`.

### `frontend/package.json`

This lists frontend dependencies and useful commands:

- `npm run dev`: starts the local development server.
- `npm run build`: checks TypeScript and produces the deployable production files in `frontend/dist`.

### `backend/app/main.py`

This is the backend entry point and the most important server file. It creates the FastAPI app and includes:

- CORS configuration so the Vercel website can call the Render API.
- `/health` for checking if the API is online.
- `/auth/register` and `/auth/login` for real account authentication.
- Password hashing with bcrypt; plaintext passwords are never saved.
- Signed JWT login tokens.
- Database initialization that creates tables when they do not exist. It does not delete existing tables or records.
- Chat endpoints to list, create, open, rename, archive, restore, search, and delete chats.
- Message endpoints to send, regenerate, and edit messages safely.
- File upload endpoints with ownership checks, allowed file types, and size limits.
- A file deletion path that removes the stored file metadata and local file only after the user confirms.

### `backend/requirements.txt`

These are the packages the backend needs. Render installs them during deployment. Important packages include FastAPI, Uvicorn, PostgreSQL support, JWT/password security libraries, `python-multipart` for uploads, and `pypdf` for text-based PDFs.

### `chatbot.py`

This is the original useful chatbot logic that the FastAPI backend reuses. It detects whether a prompt is related to Python, uses local knowledge-base answers when appropriate, understands follow-up questions from the chat context, and calls OpenRouter only from the backend.

### `config.py`

This keeps Python-learning configuration in one place: keywords, curated answers, prompts, and model-related settings. When you want to improve a built-in explanation for a Python topic, this is the first file to inspect.

### `.env`, `.env.example`, and `.gitignore`

- `.env` is private and contains real values. It must never be committed or sent to another person.
- `.env.example` is safe to commit. It contains only variable names and fake placeholder values.
- `.gitignore` tells Git to exclude real secrets, uploads, Python caches, Node packages, and generated builds.

## 5. Requirements before you start

Install these once:

1. **Python 3.11 or 3.12.** Python 3.13 may work, but a project with compiled dependencies is generally easiest on 3.11 or 3.12.
2. **Node.js 20 LTS or newer**, which includes npm. Check with `node --version` and `npm --version`.
3. **Git** for saving code history and pushing to GitHub.
4. A **Neon** PostgreSQL project.
5. An **OpenRouter** API key.
6. A **Render** account for the backend and a **Vercel** account for the frontend.

VS Code is recommended, but not required.

## 6. Environment variables and secrets

Environment variables are private configuration values. They let one codebase work locally and online without placing passwords in source files.

### Backend variables (private)

Put these in `backend/.env` for local development, or in Render's Environment page for production:

```env
DATABASE_URL=postgresql://your-neon-user:your-neon-password@your-host/neondb?sslmode=require
OPENROUTER_API_KEY=your_openrouter_key
JWT_SECRET=make-this-a-long-random-secret
ALLOWED_ORIGINS=http://localhost:5173
```

For production, `ALLOWED_ORIGINS` should contain the Vercel website URL, for example:

```env
ALLOWED_ORIGINS=https://pyguide-five.vercel.app,http://localhost:5173
```

Do not put quotes around a value unless the service specifically tells you to. Do not upload this file to GitHub.

The backend also supports the root `.env` for older local setups. To avoid confusion, prefer `backend/.env` and do not keep conflicting values in both locations.

### Frontend variable (public)

Put this in `frontend/.env` locally or Vercel's Environment Variables page:

```env
VITE_API_BASE_URL=http://localhost:8000
```

In production replace it with:

```env
VITE_API_BASE_URL=https://pyguide.onrender.com
```

Only this public API URL belongs in the frontend. Every variable beginning with `VITE_` can be visible to website visitors. Never use `VITE_DATABASE_URL`, `VITE_OPENROUTER_API_KEY`, or `VITE_JWT_SECRET`.

## 7. Run the project locally

Open **two PowerShell terminals** in the project root folder.

### Step A: start the backend

In terminal 1:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` using VS Code. Fill in the real private values from the previous section. Then start the backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

Leave this terminal running. Visit `http://localhost:8000/health`. A successful result is:

```json
{"status":"online"}
```

### Step B: start the frontend

In terminal 2:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

Check that `frontend/.env` contains:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Start the UI:

```powershell
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

### Step C: stop the servers

Click the terminal and press `Ctrl + C`. If you activated a virtual environment, type `deactivate` afterwards if desired.

## 8. Use the application

### Account and login

1. Open the site.
2. Select **Create a new account** if you are new.
3. Enter a valid email and a password with at least eight characters.
4. Sign in after registration.

The backend validates the request. A successful login returns a signed token, which lets the browser request only that user's chats.

### Chat actions

- **New Chat** clears the active view. It does not create an empty database chat.
- Send the first message to create the conversation and an automatic title.
- Use the search field to search chat titles and saved message content.
- Use a chat row's three-dot button to rename, archive, or permanently delete it.
- Use the user-message edit action to revise a question. Later stale responses are discarded and a fresh answer is generated.
- Use copy and regenerate actions on messages as needed.

### Mobile use

On a phone, tap the menu icon in the top header to open the sidebar. Tap the arrow, backdrop, a navigation item, or press Escape to close it. The chat stays full width while the sidebar is closed.

The interface is deliberately larger on phones: 16px body text, 44px+ touch targets, wide messages, and a fixed composer at the bottom.

## 9. Database and user privacy

Neon is a managed PostgreSQL database. The backend initializes these tables without deleting existing data:

| Table | Stores |
| --- | --- |
| `pyguide_users` | Email, password hash, created time |
| `pyguide_chats` | A user's chat title, archived status, timestamps |
| `pyguide_messages` | User and assistant message content and timestamps |
| `pyguide_attachments` | File metadata and the saved local storage path |
| `pyguide_message_attachments` | Which message used which attachment |
| `pyguide_user_settings` (if created) | User-level UI preferences |

Every database operation receives the authenticated user from the JWT. The API checks that chat IDs and file IDs belong to that same user. A person cannot access another person's chat simply by changing a URL or ID in the browser.

When a chat is permanently deleted, the backend deletes associated attachment metadata and the corresponding local upload files. Archiving is different: it hides a chat but keeps its data until it is restored or deleted.

## 10. Files and attachments

Use the **+** button in the composer and choose an upload option. Before sending, selected files appear as removable chips. Once sent, they are connected to that message and visible in the **Files** area.

### Supported files

- `.py`, `.txt`, `.md`, `.csv`, `.json`, `.log`
- Text-based `.pdf`
- `.png`, `.jpg`, `.jpeg`, `.webp` for storage/download only

Rules:

- Up to 8 selected files at a time.
- Maximum 5 MB per file.
- Files are validated by extension and server-side handling. Uploaded code is never executed.
- Text is extracted from supported documents and supplied only as context for the message that includes it.

### Important limits

- A text model cannot understand images unless a vision-capable model and image pipeline are added. PyGuide stores images but does not claim to analyze them.
- Scanned PDFs are images inside a PDF. They require OCR, which is not currently configured.
- `backend/uploads` is local server storage. On a Render redeploy or a server restart, local files may disappear. For permanent production files, add S3, Cloudinary, or another object storage service before relying on uploads long-term.

## 11. Deploy to Neon, Render, and Vercel

Deployment means publishing the backend and frontend so others can use them online.

### A. Neon database

1. Sign in to Neon and create or open your database project.
2. Copy the PostgreSQL connection string from the Neon dashboard.
3. In Render, add it as the private `DATABASE_URL` environment variable.
4. Do not paste it into React, Vercel, public GitHub, screenshots, or frontend `.env` files.
5. On the first successful backend startup, tables are created if missing. Existing rows are not dropped.

### B. Render backend

1. Push the repository to GitHub without `.env` files.
2. In Render choose **New +** → **Web Service** → connect the repository.
3. Set **Root Directory** to `backend`.
4. Set **Build Command** to:

   ```text
   pip install -r requirements.txt
   ```

5. Set **Start Command** to:

   ```text
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

6. Add these Render environment variables:

   ```text
   DATABASE_URL
   OPENROUTER_API_KEY
   JWT_SECRET
   ALLOWED_ORIGINS
   ```

7. Deploy. Open `https://your-render-service.onrender.com/health` and check for `{"status":"online"}`.

For your current service, the backend base URL is `https://pyguide.onrender.com`. Do not add a trailing slash to the frontend variable.

### C. Vercel frontend

1. In Vercel choose **Add New** → **Project** → import the same GitHub repository.
2. Set **Root Directory** to `frontend`.
3. Vercel detects Vite. The normal build command is `npm run build` and output directory is `dist`.
4. Add this environment variable:

   ```text
   VITE_API_BASE_URL=https://pyguide.onrender.com
   ```

5. Deploy and open the Vercel URL.

For your current site, that URL is `https://pyguide-five.vercel.app`.

### D. Connect both services with CORS

Render must accept requests from the Vercel browser site. In Render set:

```text
ALLOWED_ORIGINS=https://pyguide-five.vercel.app,http://localhost:5173
```

Save the variable and redeploy Render. Then redeploy Vercel after changing `VITE_API_BASE_URL`. If one side has an old value, login and chat calls may fail.

## 12. Test before sharing

Run this checklist locally, then repeat the important parts after deployment.

### Build checks

```powershell
cd frontend
npm run build
```

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m py_compile app\main.py
```

### Manual checklist

- [ ] `/health` says online.
- [ ] A new account can register and log in.
- [ ] Invalid email/password produces a useful error.
- [ ] A first message creates one chat, not multiple empty chats.
- [ ] A Python question receives an answer.
- [ ] An unrelated question receives the polite Python-only response.
- [ ] A Python question mentioning movies or sports is accepted when it is genuinely programming-related.
- [ ] Recent chat opens after a page refresh.
- [ ] Search finds chat title and message content.
- [ ] Rename, archive, restore, and delete work.
- [ ] Edit replaces obsolete answers with a new answer.
- [ ] A `.py` or `.txt` attachment is sent and can be used for explanation.
- [ ] The Files screen shows uploaded files, correct count, download, and delete controls.
- [ ] Deleting a conversation removes its uploaded file metadata and local stored file.
- [ ] On a 375px phone viewport, the sidebar opens as a drawer and the chat remains readable.
- [ ] On desktop, the sidebar collapses and expands cleanly.

## 13. Troubleshooting

| Problem | Most likely reason | What to do |
| --- | --- | --- |
| Status shows Offline | Backend is not running or Vite has wrong API URL | Start FastAPI; verify `/health`; check `VITE_API_BASE_URL`. |
| `signal timed out` | Render cold start, network delay, or provider delay | Wait for Render to wake, retry once, and inspect Render logs. The frontend has a longer request timeout to avoid duplicate messages. |
| Browser says CORS error | Render does not allow the frontend origin | Set `ALLOWED_ORIGINS` to exact Vercel URL and localhost, then redeploy Render. |
| Register/login gives 422 | Invalid request fields or old frontend bundle | Enter valid email and password (8+ chars), hard refresh, then check backend logs. |
| Login works locally but not Vercel | Vercel is pointing to localhost | Set Vercel `VITE_API_BASE_URL` to the Render URL, not `localhost`. Redeploy. |
| Files count is wrong | Older client view or an upload did not complete | Refresh chats/files; confirm upload response in Network tab; check `/uploads` request status. |
| Uploaded file disappears on Render | Local Render disk is not permanent | Use object storage for long-term files; do not rely on `backend/uploads` in production. |
| `chrome-extension://invalid` in Console | A browser extension injected a failing request | This is not a PyGuide code error. Test in Incognito with extensions disabled. |
| React DevTools message appears | React development information | It is informational, not an application error. Production builds do not show it. |
| Mobile UI looks tiny | Browser may be displaying an old Vite bundle/cache | Hard refresh with `Ctrl + Shift + R`; stop/start `npm run dev`; verify the 16px/48px mobile CSS rules in `style.css`. |

## 14. Safe future changes

Before changing code:

1. Make a Git commit first so you can recover.
2. Change one feature at a time.
3. Run `npm run build` after frontend changes.
4. Run `python -m py_compile app\main.py` after backend changes.
5. Test locally before pushing.
6. Never add API keys or database URLs to code.

### Examples

**Change a color or mobile size**

Edit `frontend/src/style.css`. Desktop rules are near the top. Phone rules are in the media queries near the bottom. Test at 375px width in browser DevTools.

**Change a welcome sentence or button label**

Search in `frontend/src/main.tsx` for the exact visible text. Edit it, save, and Vite refreshes the browser.

**Add a knowledge-base answer**

Edit the appropriate knowledge-base/configuration section in `config.py`. Keep answers beginner-friendly. Test the prompt locally.

**Add a protected backend feature**

Add a typed request model and endpoint in `backend/app/main.py`. Use the existing authentication helper and always filter database operations by the authenticated user's ID.

**Add permanent file storage**

Do not put large binaries directly into PostgreSQL. Use object storage and save only metadata/URLs in `pyguide_attachments`. Keep ownership checks and delete cleanup.

## 15. Git basics

Git saves snapshots of code. GitHub hosts those snapshots online.

Check what changed:

```powershell
git status
```

Review changes:

```powershell
git diff
```

Save a safe change:

```powershell
git add README.md PROJECT_GUIDE.md frontend/src backend/app
git commit -m "Improve PyGuide documentation and mobile UI"
git push origin main
```

Before any `git add`, run `git status` and make sure `.env`, `backend/uploads`, `.venv`, `node_modules`, and `dist` are not staged. If a secret was pushed accidentally, removing it in a later commit is not enough: rotate the secret in the provider dashboard and remove it from Git history with help from an experienced developer.

---

## Final handover reminder

The codebase is intentionally split into a frontend and backend because this is the safe production design. Keep private credentials only on the backend/Render side. Keep `PROJECT_GUIDE.md` with the repository so the next person can understand how to run, change, test, and deploy PyGuide without needing to guess.
