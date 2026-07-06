"""
============================================================================
BACKEND API - Prediksi Harga Rumah California (Model 1: DNN tanpa PCA)
============================================================================
Menjalankan:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Struktur folder yang diharapkan (relatif terhadap file ini):
    backend/
      main.py
      schemas.py
      requirements.txt
      outputs/
        best_dnn_nopca.keras
        preprocessor.pkl
        y_scaler.pkl
        meta.json

Salin folder `outputs/` hasil training (dari script training) ke dalam
folder backend/ ini sebelum menjalankan server.
============================================================================
"""

from contextlib import asynccontextmanager
from pathlib import Path
import json
import logging

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from schemas import (
    HouseFeaturesRequest,
    PredictionResponse,
    HealthResponse,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("house-price-api")

MODEL_DIR = Path(__file__).parent / "outputs"

# Wadah global untuk artefak yang di-load sekali saat startup
ml_artifacts: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model & preprocessor sekali saat startup (bukan per-request)."""
    logger.info("Loading model artifacts from %s ...", MODEL_DIR)
    try:
        # Import di sini agar startup gagal dengan pesan jelas jika
        # tensorflow/sklearn belum terpasang, tanpa membuat modul gagal
        # di-import lebih awal.
        from model_arch import build_dnn

        with open(MODEL_DIR / "meta.json") as f:
            meta = json.load(f)

        preprocessor = joblib.load(MODEL_DIR / "preprocessor.pkl")
        y_scaler = joblib.load(MODEL_DIR / "y_scaler.pkl")
        pca = None
        if meta.get("use_pca"):
            pca = joblib.load(MODEL_DIR / "pca.pkl")
            n_features = pca.n_components_
        else:
            # Jumlah fitur setelah preprocessing (numerik + one-hot),
            # dihitung dari preprocessor -- tidak di-hardcode agar selalu
            # cocok dengan preprocessor.pkl yang sedang dipakai.
            n_features = len(preprocessor.get_feature_names_out())

        # Bangun ulang arsitektur di kode (bukan load_model dari file
        # .keras utuh), lalu load weights saja. Ini menghindari error
        # ketidakcocokan format model.get_config() antar versi Keras
        # (mis. "Unrecognized keyword arguments ... quantization_config").
        model = build_dnn(n_features)
        weights_file = meta.get(
            "weights_file", meta["model_file"].replace(".keras", ".weights.h5")
        )
        model.load_weights(str(MODEL_DIR / weights_file))

        ml_artifacts["model"] = model
        ml_artifacts["preprocessor"] = preprocessor
        ml_artifacts["y_scaler"] = y_scaler
        ml_artifacts["pca"] = pca
        ml_artifacts["meta"] = meta
        logger.info("Model artifacts loaded. use_pca=%s", meta.get("use_pca"))
    except Exception:
        logger.exception("Gagal memuat artefak model saat startup")
        ml_artifacts["model"] = None
    yield
    ml_artifacts.clear()


app = FastAPI(
    title="California House Price Prediction API",
    description="API untuk memprediksi median_house_value menggunakan Model 1 (DNN tanpa PCA)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: dibuka lebar agar bisa diakses dari emulator Android (10.0.2.2),
# iOS simulator, dan perangkat fisik di jaringan lokal. Untuk produksi,
# sebaiknya batasi allow_origins ke domain/app tertentu.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Terjadi kesalahan pada server: {str(exc)}"},
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    model_loaded = ml_artifacts.get("model") is not None
    use_pca = bool(ml_artifacts.get("meta", {}).get("use_pca", False))
    return HealthResponse(
        status="ok" if model_loaded else "model_not_loaded",
        model_loaded=model_loaded,
        use_pca=use_pca,
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        400: {"description": "Input tidak valid"},
        500: {"description": "Kesalahan server / model gagal dijalankan"},
    },
)
async def predict(payload: HouseFeaturesRequest):
    if ml_artifacts.get("model") is None:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Model belum siap. Coba lagi beberapa saat, atau cek log server."},
        )

    try:
        preprocessor = ml_artifacts["preprocessor"]
        y_scaler = ml_artifacts["y_scaler"]
        model = ml_artifacts["model"]
        pca = ml_artifacts["pca"]

        raw = payload.model_dump()
        df = pd.DataFrame([raw])

        X_proc = preprocessor.transform(df).astype(np.float32)
        if pca is not None:
            X_proc = pca.transform(X_proc).astype(np.float32)

        pred_scaled = model.predict(X_proc, verbose=0).ravel()[0]
        prediction = float(
            y_scaler.inverse_transform([[pred_scaled]]).ravel()[0]
        )
        # Harga tidak boleh negatif secara logis
        prediction = max(prediction, 0.0)

        return PredictionResponse(predicted_price=round(prediction, 2))

    except Exception as e:
        logger.exception("Prediction failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Gagal melakukan prediksi: {str(e)}"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)