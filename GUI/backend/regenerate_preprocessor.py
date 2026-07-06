"""
Regenerate preprocessor.pkl & y_scaler.pkl memakai scikit-learn versi
BACKEND ANDA SAAT INI (bukan versi Colab), agar tidak ada lagi masalah
"InconsistentVersionWarning" / gagal unpickle.

Prosesnya deterministik: split data & fit preprocessing menggunakan
random_state yang SAMA PERSIS dengan script training asli, sehingga
hasilnya identik dengan yang dipakai saat training model.

Cara pakai:
1. Taruh housing.csv di folder backend/ ini (sejajar dengan file ini).
2. Jalankan:  python regenerate_preprocessor.py
3. File outputs/preprocessor.pkl dan outputs/y_scaler.pkl akan ditimpa
   dengan versi baru yang kompatibel dengan scikit-learn Anda.
4. Restart uvicorn.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
DATA_PATH = "housing.csv"
TARGET_COL = "median_house_value"
OUTPUT_DIR = Path("outputs")


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = X.select_dtypes(exclude=[np.number]).columns.tolist()

    numeric_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(transformers=[
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ])


def main():
    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].to_numpy(dtype=np.float32)

    # Split PERSIS SAMA seperti script training: 70/15/15
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=RANDOM_STATE
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.15 / 0.85, random_state=RANDOM_STATE
    )

    preprocessor = build_preprocessor(X_train)
    preprocessor.fit(X_train)

    target_scaler = StandardScaler()
    target_scaler.fit(y_train.reshape(-1, 1))

    joblib.dump(preprocessor, OUTPUT_DIR / "preprocessor.pkl")
    joblib.dump(target_scaler, OUTPUT_DIR / "y_scaler.pkl")

    n_features = len(preprocessor.get_feature_names_out())
    print(f"Selesai. Jumlah fitur setelah preprocessing: {n_features}")
    print("preprocessor.pkl dan y_scaler.pkl sudah ditimpa di folder outputs/.")


if __name__ == "__main__":
    main()