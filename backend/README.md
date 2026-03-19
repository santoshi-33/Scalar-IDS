# IDS Backend (FastAPI)

## Run locally

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment variables
- `MODEL_PATH`: path to `ids_model.joblib` (default: `backend/app/artifacts/ids_model.joblib`)
- `ALLOWED_ORIGINS`: comma-separated list (default: `http://localhost:4200,http://localhost:4201`)

