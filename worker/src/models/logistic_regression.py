import joblib
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent / "models" / "models_data" / "logistic_regression_model.joblib"

def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def predict(data):
    model = load_model()
    return model.predict(data).tolist()
