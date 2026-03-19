# Deploy to Render

This repo contains:
- `backend/`: FastAPI ML inference service (Docker)
- `fyp-web/`: Angular frontend (static site)

## Backend (FastAPI)

1. Create a **Web Service** on Render.
2. Choose **Docker**.
3. Root directory: `backend`
4. Expose port: `8000`
5. Set env vars:
   - `MODEL_PATH=/app/app/artifacts/ids_model.joblib`
   - `ALLOWED_ORIGINS=https://<your-frontend>.onrender.com`

Health endpoint: `/health`

## Frontend (Angular)

1. Create a **Static Site**.
2. Root directory: repo root
3. Build command:

```bash
cd fyp-web && npm ci && npm run build
```

4. Publish directory:
- `fyp-web/dist/fyp-web/browser`

## Using `render.yaml`

You can also deploy with the included `render.yaml` as a Blueprint. Replace the placeholder frontend URL in `ALLOWED_ORIGINS`.

