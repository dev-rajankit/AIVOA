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

| Component            | Status       | Notes                                          |
| -------------------- | ------------ | ---------------------------------------------- |
| React frontend       | ✅ Scaffold  | Vite + React 19, placeholder page              |
| FastAPI backend       | ✅ Running   | Health endpoint, CORS configured               |
| PostgreSQL           | ✅ Docker    | docker-compose with healthcheck                |
| SQLAlchemy models    | ✅ Complete  | 4 tables, enums, indexes, relationships        |
| Alembic migrations   | ✅ Complete  | Async-aware, initial migration generated       |
| LangGraph agent      | 🔲 Planned   | Chunk 3–4                                      |
| Groq LLM integration | 🔲 Planned   | Chunk 3                                        |
| Redux Toolkit        | 🔲 Planned   | Chunk 5                                        |
| Complaint form UI    | 🔲 Planned   | Chunk 5–6                                      |
| Risk/CAPA assessment | 🔲 Planned   | Chunk 8                                        |
| PDF/email parsing    | 🔲 Planned   | Chunk 7                                        |

### Current Status

```
Chunk 2 — Database Layer
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

### 3b. Run database migrations

```bash
cd backend
alembic upgrade head
```

This creates the `complaints`, `risk_assessments`, `audit_log`, and `copilot_messages` tables.

### 3c. Seed sample data (optional)

```bash
cd backend
python -m app.db.seed
```

Inserts two sample complaints (one FDF, one API) for manual testing.

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

## Database

PostgreSQL is the **system of record** for all complaint data. Every AI-driven change is persisted alongside an audit trail, satisfying pharma regulatory requirements (21 CFR Part 11).

### Core Tables

| Table              | Purpose                                              |
| ------------------ | ---------------------------------------------------- |
| `complaints`       | Central complaint record (AI-populated fields)       |
| `risk_assessments` | AI-generated risk/CAPA assessments (versioned)       |
| `audit_log`        | Immutable change history (who changed what, when)    |
| `copilot_messages` | Multi-turn chat history for page refresh persistence |

### Key Design Decisions

- **UUID primary keys**: globally unique, safe for future multi-tenant/distributed scenarios, no sequential-ID enumeration risk.
- **complaint_number**: separate human-readable business identifier (`CC-2026-00154`). Decoupled from the PK so it can follow business formatting rules.
- **JSONB for raw_extraction_json**: stores the exact LLM output for every complaint. Enables debugging, re-processing, and audit without re-calling the LLM. PostgreSQL-native JSONB supports indexing if needed later.
- **Versioned risk assessments**: stored as separate rows (not 1:1 overwrite) so assessment history is preserved as more complaint info is provided.
- **Audit log**: every field change by the AI produces one row — this powers both compliance reporting and the frontend's field-highlight "diff" effect.

### Indexes

| Index                             | Reason                                 |
| --------------------------------- | -------------------------------------- |
| `complaint_number` (unique)       | Business identifier lookups            |
| `batch_lot_number`                | Duplicate detection queries            |
| `session_id` (copilot_messages)   | Efficient conversation retrieval       |
| `(complaint_id, created_at)` (audit_log) | Chronological audit trail queries |

### Migrations

Alembic manages schema migrations with async support (asyncpg). The initial migration creates all four tables, PostgreSQL enum types, indexes, and foreign key constraints.

```bash
cd backend
alembic upgrade head     # apply migrations
alembic downgrade -1     # rollback last migration
alembic history          # view migration history
```

---

## Async Architecture

The backend is built async-first (`async def` endpoints, async-compatible structure). This is deliberate because the production workflow involves:

1. Multiple sequential LLM API calls per complaint (extraction → merge → risk assessment)
2. Database reads/writes between agent nodes
3. Concurrent users submitting complaints simultaneously

Blocking the event loop on any of these would starve other requests. The async foundation ensures that SQLAlchemy (asyncpg), Groq's async client, and FastAPI all share the same event loop without blocking.

---

## Project Structure

```
AIVOA/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── core/
│   │   │   └── config.py        # pydantic-settings configuration
│   │   └── db/
│   │       ├── models.py        # SQLAlchemy ORM models (4 tables)
│   │       ├── session.py       # Async engine & session factory
│   │       └── seed.py          # Sample data for testing
│   ├── alembic/
│   │   ├── env.py               # Async migration environment
│   │   └── versions/            # Migration scripts
│   ├── tests/
│   │   ├── test_health.py       # Health endpoint tests
│   │   └── test_models.py       # Model/metadata tests (18 tests)
│   ├── alembic.ini
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
