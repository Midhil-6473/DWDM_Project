# DWDM Crop Yield Full-Stack App

This project now includes:
- `backend/` FastAPI service for model prediction + CSV analytics
- `frontend/` React dashboard UI for state/category inputs and visualization charts

## Dataset filename

The backend is configured to use:
- `crop_yiled_cleaned_dataset.csv` (as requested)

If this file is not present, it automatically falls back to:
- `crop_yield_cleaned_dataset.csv`

## Run backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

Optional API URL override:

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

## Main endpoints

- `GET /meta/form` - dynamic form metadata + model metrics
- `POST /predict/both` - classification + regression prediction
- `GET /analytics/summary` - filtered summary by `state`, `crop_type`, `season`
- `GET /analytics/yield_distribution` - filtered yield distribution
- `GET /analytics/category_counts` - filtered category counts
- `GET /analytics/state_crop_comparison` - selected average vs dataset average vs predicted yield
