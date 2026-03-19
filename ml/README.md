# ML training (IDS)

This trains a simple baseline model and exports a single **preprocessing + model** pipeline artifact for the FastAPI backend.

## Train

```bash
pip install -r backend/requirements.txt
python ml/train.py --data path/to/dataset.csv --label-col label
```

## Output
- `backend/app/artifacts/ids_model.joblib`

