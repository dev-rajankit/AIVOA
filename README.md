# AIVOA

**AI-Powered Customer Complaint Management System** for pharmaceutical quality management (QMS).

AIVOA automates complaint intake, triage, and risk assessment for pharmaceutical companies, supporting both API (Active Pharmaceutical Ingredient) and FDF (Finished Dosage Form) product lines. An AI Copilot processes natural-language complaints and document uploads, populates structured complaint forms, and generates risk assessments — all grounded in regulatory frameworks (21 CFR §211.198, ICH Q9/Q10).

---

## Architecture

```
React (Vite)
  ↓  HTTP API
FastAPI
  ↓
LangGraph Agent        ← future chunk
  ↓
Groq LLM              ← future chunk
  (gpt-oss-20b / gpt-oss-120b)
  ↓
PostgreSQL
```

### Component Status

| Component            | Status       | Notes                                   |
| -------------------- | ------------ | --------------------------------------- |
| React frontend       | ✅ Scaffold  | Vite + React 19, placeholder page       |
| FastAPI backend       | ✅ Running   | Health endpoint, CORS configured        |
| PostgreSQL           | ✅ Docker    | docker-compose with healthcheck         |
| LangGraph agent      | 🔲 Planned   | Chunk 2–4                               |
| Groq LLM integration | 🔲 Planned   | Chunk 3                                 |
| Redux Toolkit        | 🔲 Planned   | Chunk 5                                 |
| Complaint form UI    | 🔲 Planned   | Chunk 5–6                               |
| Risk/CAPA assessment | 🔲 Planned   | Chunk 8                                 |
| PDF/email parsing    | 🔲 Planned   | Chunk 7                                 |

### Current Status

```
Chunk 1 — Project Foundation
```

---

## Requirements

| Tool       | Minimum Version |
| ---------- | --------------- |
| Python     | 3.11+           |
| Node.js    | 18+             |
| npm        | 9+              |
| Docker     | 24+             |
| Git        | 2.40+           |

---

## Setup

### 1. Clone the project

```bash
git clone <repo-url>
cd AIVOA
```

### 2. Environment configuration

```bash
cp .env.example .env
# Edit .env with your actual values (Groq API key, etc.)
```

> ⚠️ Never commit `.env` — it is gitignored. Only `.env.example` is tracked.

### 3. Start PostgreSQL

```bash
docker-compose up -d
```

Verify it's healthy:

```bash
docker-compose ps
```

### 4. Backend setup

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 5. Run FastAPI

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Verify: open [http://localhost:8000/health](http://localhost:8000/health) — should return `{"status": "ok"}`

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Run backend tests

```bash
cd backend
pytest -v
```

### 7. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173)

---

## Async Architecture

The backend is built async-first (`async def` endpoints, async-compatible structure). This is deliberate because the production workflow involves:

1. Multiple sequential LLM API calls per complaint (extraction → merge → risk assessment)
2. Database reads/writes between agent nodes
3. Concurrent users submitting complaints simultaneously

Blocking the event loop on any of these would starve other requests. The async foundation established in Chunk 1 ensures that future chunks (async SQLAlchemy with asyncpg, async Groq client) integrate naturally without architectural refactoring.

---

## Project Structure

```
AIVOA/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_health.py       # Health endpoint tests
│   ├── requirements.txt
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx              # Root component
│   │   ├── App.css              # Component styles
│   │   └── index.css            # Global styles & design tokens
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── .env.example                  # Environment template
├── .gitignore
├── docker-compose.yml            # PostgreSQL for development
├── AIVOA_Assignment_Architecture_Plan.md
└── README.md
```

---

## License

Private — AIVOA AI Product Engineer Intern Assignment.
