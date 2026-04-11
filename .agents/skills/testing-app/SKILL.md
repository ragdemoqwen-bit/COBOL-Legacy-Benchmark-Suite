# Testing the Portfolio Management System (COBOL-to-Python Migration)

## Running the App Locally

```bash
# Install dependencies
cd python_migration && pip install -e ".[dev]"

# Start the FastAPI server
cd python_migration/src && PYTHONPATH=. uvicorn api.app:app --host 0.0.0.0 --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- SQLite DB created at `python_migration/src/portfolio_mgmt.db` on first startup

## Running Tests & Lint

```bash
cd python_migration && python -m pytest src/tests/ -v    # 99 unit tests
cd python_migration && ruff check src/                   # lint
```

## Key API Endpoints to Test

### Health
- `GET /health` — returns `{"status": "healthy", "database": "connected"}`
- `GET /status` — returns system info with version

### Portfolio CRUD
- `POST /portfolios/` — create (HTTP 201)
- `GET /portfolios/{id}` — read (HTTP 200)
- `PUT /portfolios/{id}` — update (HTTP 200)
- `DELETE /portfolios/{id}` — delete (HTTP 204)
- `GET /portfolios/` — list all (HTTP 200)
- Duplicate create returns HTTP 409

### Batch Jobs
- `POST /batch/jobs/{name}/init` — initialize
- `GET /batch/jobs/{name}/check` — check prerequisites
- `GET /batch/jobs` — list jobs
- `POST /batch/jobs/{name}/terminate` — terminate

## Common Pitfalls

- The app must be started from `python_migration/src/` with `PYTHONPATH=.` set, otherwise imports fail
- `pyproject.toml` sets `pythonpath = ["src"]` for pytest, but uvicorn needs explicit `PYTHONPATH=.`
- Delete the SQLite DB file to reset state between test runs: `rm -f python_migration/src/portfolio_mgmt.db`
- No CI is configured on this repo — all testing is manual
- Unit tests only cover service layer; no integration/route tests exist yet
