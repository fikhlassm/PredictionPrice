from __future__ import annotations

import time
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend, biar tidak buka jendela & tidak nge-block
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# KONFIGURASI GLOBAL (reproducibility, style, path output)
warnings.filterwarnings("ignore", category=UserWarning)
sns.set_theme(style="whitegrid")   # tema visual profesional untuk EDA

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

DATA_PATH = "housing.csv"
TARGET_COL = "median_house_value"
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Ambang variansi kumulatif yang ingin dipertahankan oleh PCA (95%)
PCA_VARIANCE_THRESHOLD = 0.95


# Helper: simpan plot ke file (menggantikan plt.show yang bikin nge-block)
def save_plot(filename: str) -> None:
    """Simpan figure matplotlib aktif ke folder outputs, lalu tutup."""
    path = OUTPUT_DIR / filename
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close("all")
    print(f"  [plot tersimpan] {path}")


# TAHAP 1 - ANALISIS DATASET
def load_dataset(path: str) -> pd.DataFrame:
    """Memuat dataset CSV menjadi DataFrame."""
    return pd.read_csv(path)


def analyze_dataset(df: pd.DataFrame) -> None:
    print("TAHAP 1 - ANALISIS DATASET")

    print(f"[Shape] {df.shape[0]} baris x {df.shape[1]} kolom\n")

    print("[info()]")
    df.info()

    print("\n[describe()]")
    print(df.describe().round(2).T)

    print("\n[Tipe data]")
    print(df.dtypes)

    print("\n[Missing value per kolom]")
    print(df.isnull().sum())

    n_dup = df.duplicated().sum()
    print(f"\n[Duplikat] {n_dup} baris duplikat")

    print("\n[Distribusi kategori 'ocean_proximity']")
    print(df["ocean_proximity"].value_counts())

    print(f"\n[Distribusi target '{TARGET_COL}']")
    print(df[TARGET_COL].describe().round(2))
    print(f"Skewness target: {df[TARGET_COL].skew():.3f}")

    print("\n[Korelasi fitur numerik terhadap target]")
    corr = df.corr(numeric_only=True)[TARGET_COL].sort_values(ascending=False)
    print(corr.round(3))


# TAHAP 2 - EXPLORATORY DATA ANALYSIS (EDA)
def eda_visualizations(df: pd.DataFrame) -> None:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # --- (a) Histogram seluruh fitur numerik --------------------------------
    df[numeric_cols].hist(bins=40, figsize=(14, 10), color="#4C72B0",
                          edgecolor="white")
    plt.suptitle("Histogram Seluruh Fitur Numerik", fontsize=14)
    plt.tight_layout()
    save_plot("eda_01_histogram.png")

    # --- (b) Boxplot fitur numerik (deteksi outlier) ------------------------
    fig, axes = plt.subplots(3, 3, figsize=(14, 10))
    for ax, col in zip(axes.ravel(), numeric_cols):
        sns.boxplot(y=df[col], ax=ax, color="#55A868")
        ax.set_title(col)
    for ax in axes.ravel()[len(numeric_cols):]:
        ax.set_visible(False)
    plt.suptitle("Boxplot Fitur Numerik (Deteksi Outlier)", fontsize=14)
    plt.tight_layout()
    save_plot("eda_02_boxplot.png")

    # --- (c) Correlation heatmap --------------------------------------------
    plt.figure(figsize=(10, 8))
    corr = df.corr(numeric_only=True)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    plt.title("Correlation Heatmap", fontsize=14)
    plt.tight_layout()
    save_plot("eda_03_heatmap.png")

    # --- (d) Distribusi target ----------------------------------------------
    plt.figure(figsize=(8, 5))
    sns.histplot(df[TARGET_COL], bins=50, kde=True, color="#C44E52")
    plt.title("Distribusi Target: median_house_value", fontsize=14)
    plt.tight_layout()
    save_plot("eda_04_target_dist.png")

    # --- (e) Scatter fitur terpenting (median_income) vs target -------------
    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df, x="median_income", y=TARGET_COL,
                    alpha=0.3, s=12, color="#4C72B0")
    plt.title("median_income vs median_house_value", fontsize=14)
    plt.tight_layout()
    save_plot("eda_05_income_vs_target.png")

    # --- (f) Sebaran geografis harga rumah ----------------------------------
    plt.figure(figsize=(8, 6))
    sc = plt.scatter(df["longitude"], df["latitude"], c=df[TARGET_COL],
                     cmap="viridis", alpha=0.4, s=10)
    plt.colorbar(sc, label="median_house_value")
    plt.xlabel("longitude")
    plt.ylabel("latitude")
    plt.title("Sebaran Geografis Harga Rumah di California", fontsize=14)
    plt.tight_layout()
    save_plot("eda_06_geografis.png")

    # --- (g) Pairplot subset fitur penting -----------------------------------
    subset = ["median_income", "housing_median_age", "total_rooms",
              TARGET_COL]
    pair = sns.pairplot(df[subset].sample(2000, random_state=RANDOM_STATE),
                        diag_kind="kde", plot_kws={"alpha": 0.3, "s": 12})
    pair.figure.suptitle("Pairplot Fitur Penting (sampel 2000)", y=1.02)
    save_plot("eda_07_pairplot.png")


# TAHAP 3 & 4 - PREPROCESSING (ANTI-LEAKAGE) + SPLITTING + PCA
def split_features_target(df: pd.DataFrame):
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL].to_numpy(dtype=np.float32)
    return X, y


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

    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ])
    return preprocessor


def split_preprocess_and_pca(X: pd.DataFrame, y: np.ndarray,
                             variance_threshold: float = PCA_VARIANCE_THRESHOLD):
    # --- Split dua tahap: test dulu, lalu validation dari sisa train --------
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=RANDOM_STATE
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.15 / 0.85, random_state=RANDOM_STATE
    )

    # --- Preprocessing fitur: FIT hanya di train (anti-leakage) --------------
    preprocessor = build_preprocessor(X_train)
    X_train_p = preprocessor.fit_transform(X_train).astype(np.float32)
    X_val_p = preprocessor.transform(X_val).astype(np.float32)
    X_test_p = preprocessor.transform(X_test).astype(np.float32)

    # --- PCA: FIT hanya di train (anti-leakage) ------------------------------
    pca_full = PCA(random_state=RANDOM_STATE)
    pca_full.fit(X_train_p)
    evr = pca_full.explained_variance_ratio_
    cum_evr = np.cumsum(evr)
    n_components = int(np.argmax(cum_evr >= variance_threshold) + 1)

    pca = PCA(n_components=n_components, random_state=RANDOM_STATE)
    X_train_pca = pca.fit_transform(X_train_p).astype(np.float32)
    X_val_pca = pca.transform(X_val_p).astype(np.float32)
    X_test_pca = pca.transform(X_test_p).astype(np.float32)

    # --- Target scaling: FIT hanya di y_train (anti-leakage) -----------------
    target_scaler = StandardScaler()
    y_train_s = target_scaler.fit_transform(
        y_train.reshape(-1, 1)).ravel().astype(np.float32)
    y_val_s = target_scaler.transform(
        y_val.reshape(-1, 1)).ravel().astype(np.float32)

    data = {
        "X_train_nopca": X_train_p, "X_val_nopca": X_val_p,
        "X_test_nopca": X_test_p,
        "X_train_pca": X_train_pca, "X_val_pca": X_val_pca,
        "X_test_pca": X_test_pca,
        "y_train_s": y_train_s, "y_val_s": y_val_s,
        "y_train": y_train, "y_val": y_val, "y_test": y_test,
    }
    pca_info = {"evr": evr, "cum_evr": cum_evr, "n_components": n_components}
    return data, preprocessor, pca, target_scaler, pca_info


def print_pca_summary(pca_info: dict, threshold: float) -> None:
    """Mencetak tabel explained variance ratio & komponen terpilih."""
    evr, cum_evr, n_components = (
        pca_info["evr"], pca_info["cum_evr"], pca_info["n_components"]
    )
    print("\nPCA (fit HANYA pada data train) - explained variance ratio:")
    for i, (e, c) in enumerate(zip(evr, cum_evr), start=1):
        mark = " <== terpilih" if i == n_components else ""
        print(f"  PC{i:<2d}: {e:6.4f} | kumulatif: {c:6.4f}{mark}")
    print(f"\nJumlah komponen terpilih : {n_components} "
          f"(mempertahankan {cum_evr[n_components - 1] * 100:.2f}% "
          f"informasi dari data train, threshold={threshold:.0%})")


def plot_explained_variance(pca_info: dict, threshold: float) -> None:
    """Grafik Explained Variance & Cumulative Explained Variance."""
    evr, cum_evr, n_components = (
        pca_info["evr"], pca_info["cum_evr"], pca_info["n_components"]
    )
    x = np.arange(1, len(evr) + 1)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(x, evr, color="#4C72B0", alpha=0.7,
            label="Explained variance per komponen")
    ax1.set_xlabel("Principal Component")
    ax1.set_ylabel("Explained Variance Ratio", color="#4C72B0")
    ax1.set_xticks(x)

    ax2 = ax1.twinx()
    ax2.plot(x, cum_evr, color="#C44E52", marker="o",
             label="Cumulative explained variance")
    ax2.axhline(threshold, color="gray", linestyle="--",
                label=f"Ambang {threshold:.0%}")
    ax2.axvline(n_components, color="green", linestyle=":",
                label=f"n_components = {n_components}")
    ax2.set_ylabel("Cumulative Explained Variance", color="#C44E52")
    ax2.set_ylim(0, 1.05)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="center right")

    plt.title("Explained Variance & Cumulative Explained Variance (PCA)")
    plt.tight_layout()
    save_plot("pca_explained_variance.png")


# TAHAP 5 - MEMBANGUN DEEP NEURAL NETWORK
def build_dnn(input_dim: int) -> keras.Model:
    model = keras.Sequential(name="DNN_Regressor")
    model.add(keras.Input(shape=(input_dim,)))

    for units, drop in [(256, 0.3), (128, 0.3), (64, 0.2), (32, 0.2)]:
        model.add(layers.Dense(units, kernel_initializer="he_normal"))
        model.add(layers.BatchNormalization())
        model.add(layers.Activation("relu"))
        model.add(layers.Dropout(drop))

    model.add(layers.Dense(1, activation="linear"))

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"],
    )
    return model


def get_callbacks(checkpoint_path: str):
    """EarlyStopping + ModelCheckpoint + ReduceLROnPlateau."""
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=20,
            restore_best_weights=True, verbose=1,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path, monitor="val_loss",
            save_best_only=True, verbose=0,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=8,
            min_lr=1e-6, verbose=1,
        ),
    ]


# TAHAP 6 - TRAINING
def train_model(model, X_train, y_train, X_val, y_val, checkpoint_path,
                epochs=200, batch_size=256):
    """Melatih model, mengukur waktu training, dan melaporkan epoch terbaik."""
    callbacks = get_callbacks(checkpoint_path)

    print(f"  Mulai training (maks {epochs} epoch, batch={batch_size}) ...")
    start = time.perf_counter()
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs, batch_size=batch_size,
        callbacks=callbacks, verbose=2,  # 2 = satu baris per epoch, biar kelihatan progressnya
    )
    train_time = time.perf_counter() - start

    val_losses = history.history["val_loss"]
    best_epoch = int(np.argmin(val_losses)) + 1

    print(f"  Training selesai dalam {train_time:.1f} detik "
          f"({len(val_losses)} epoch dijalankan)")
    print(f"  Epoch terbaik (val_loss minimum) : epoch ke-{best_epoch}")
    print(f"  Loss terbaik (val_loss)          : {min(val_losses):,.4f}")
    return history, train_time, best_epoch


# TAHAP 7 - EVALUASI
def evaluate_model(model, X_test, y_test, target_scaler) -> dict:
    """Menghitung MAE, MSE, RMSE, R2 pada data test (skala Dollar asli)."""
    y_pred_scaled = model.predict(X_test, verbose=0).ravel()
    y_pred = target_scaler.inverse_transform(
        y_pred_scaled.reshape(-1, 1)
    ).ravel()

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = float(np.sqrt(mse))
    r2 = r2_score(y_test, y_pred)

    print(f"  MAE  : {mae:,.2f}")
    print(f"  MSE  : {mse:,.2f}")
    print(f"  RMSE : {rmse:,.2f}")
    print(f"  R2   : {r2:.4f}")

    return {"MAE": mae, "MSE": mse, "RMSE": rmse, "R2": r2, "y_pred": y_pred}


def plot_loss_curve(history, tag: str) -> None:
    """Kurva Loss (training vs validation)."""
    plt.figure(figsize=(7, 4))
    plt.plot(history.history["loss"], label="Training loss")
    plt.plot(history.history["val_loss"], label="Validation loss")
    plt.title(f"Loss Curve - {tag}")
    plt.xlabel("Epoch")
    plt.ylabel("Loss (MSE, skala ter-standar)")
    plt.legend()
    plt.tight_layout()
    save_plot(f"loss_curve_{tag}.png")


def plot_residual(y_test, y_pred, tag: str) -> None:
    """Residual plot (error terhadap nilai prediksi)."""
    residual = y_test - y_pred
    plt.figure(figsize=(7, 4))
    plt.scatter(y_pred, residual, alpha=0.3, s=10, color="#4C72B0")
    plt.axhline(0, color="red", linestyle="--")
    plt.title(f"Residual Plot - {tag}")
    plt.xlabel("Prediksi")
    plt.ylabel("Residual (aktual - prediksi)")
    plt.tight_layout()
    save_plot(f"residual_{tag}.png")


def plot_actual_vs_pred(y_test, y_pred, tag: str) -> None:
    """Scatter Actual vs Prediction dengan garis ideal y = x."""
    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, y_pred, alpha=0.3, s=10, color="#55A868")
    lims = [min(y_test.min(), y_pred.min()), max(y_test.max(), y_pred.max())]
    plt.plot(lims, lims, color="red", linestyle="--", label="Ideal (y = x)")
    plt.title(f"Actual vs Prediction - {tag}")
    plt.xlabel("Aktual")
    plt.ylabel("Prediksi")
    plt.legend()
    plt.tight_layout()
    save_plot(f"actual_vs_pred_{tag}.png")


def count_params(model) -> int:
    """Mengembalikan total parameter (trainable + non-trainable)."""
    return int(model.count_params())


# TAHAP 9 - SIMPAN MODEL & ARTEFAK (hanya model TERBAIK, untuk backend/inference)
def save_artifacts(preprocessor, pca, target_scaler, best_name: str,
                   use_pca: bool, model_file: str, weights_file: str,
                   n_components) -> None:
    joblib.dump(preprocessor, OUTPUT_DIR / "preprocessor.pkl")
    joblib.dump(target_scaler, OUTPUT_DIR / "y_scaler.pkl")
    if use_pca and pca is not None:
        joblib.dump(pca, OUTPUT_DIR / "pca.pkl")

    meta = {
        "best_model": best_name,
        "use_pca": use_pca,
        "n_components": n_components,
        "model_file": model_file,
        "weights_file": weights_file,
    }
    with open(OUTPUT_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    extra = ", pca.pkl" if use_pca else ""
    print(f"\nArtefak model terbaik ('{best_name}') tersimpan: "
          f"{model_file}, {weights_file}, preprocessor.pkl, y_scaler.pkl, "
          f"meta.json{extra}")


# MAIN PIPELINE
def main() -> None:
    # ---- Tahap 1: Analisis dataset -----------------------------------------
    df = load_dataset(DATA_PATH)
    analyze_dataset(df)

    # ---- Tahap 2: EDA -------------------------------------------------------
    print("\n" + "=" * 70)
    print("TAHAP 2 - EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 70)
    eda_visualizations(df)

    X, y = split_features_target(df)

    # ---- Tahap 3 & 4: Preprocessing (anti-leakage) + Splitting + PCA -------
    print("\n" + "=" * 70)
    print("TAHAP 3 & 4 - PREPROCESSING (anti-leakage) + SPLITTING + PCA")
    print("=" * 70)
    data, preprocessor, pca, target_scaler, pca_info = \
        split_preprocess_and_pca(X, y)

    n_features_awal = data["X_train_nopca"].shape[1]
    print(f"Jumlah fitur setelah encoding : {n_features_awal}")
    print(f"Train      : {data['X_train_nopca'].shape[0]} sampel")
    print(f"Validation : {data['X_val_nopca'].shape[0]} sampel")
    print(f"Test       : {data['X_test_nopca'].shape[0]} sampel")

    print_pca_summary(pca_info, PCA_VARIANCE_THRESHOLD)
    plot_explained_variance(pca_info, PCA_VARIANCE_THRESHOLD)

    results = {}

    # =========================================================================
    # MODEL 1 : DNN TANPA PCA (baseline)
    # =========================================================================
    print("\n" + "#" * 70)
    print("# MODEL 1 : DNN TANPA PCA (baseline)")
    print("#" * 70)
    model1 = build_dnn(input_dim=n_features_awal)
    hist1, time1, best_ep1 = train_model(
        model1, data["X_train_nopca"], data["y_train_s"],
        data["X_val_nopca"], data["y_val_s"],
        checkpoint_path=str(OUTPUT_DIR / "best_dnn_nopca.keras"),
    )
    print("\n  [Evaluasi Model 1 - data test, skala Dollar]")
    eval1 = evaluate_model(model1, data["X_test_nopca"], data["y_test"],
                           target_scaler)
    plot_loss_curve(hist1, "Model1_NoPCA")
    plot_residual(data["y_test"], eval1["y_pred"], "Model1_NoPCA")
    plot_actual_vs_pred(data["y_test"], eval1["y_pred"], "Model1_NoPCA")
    results["Model 1 (DNN tanpa PCA)"] = {
        "MAE": eval1["MAE"], "MSE": eval1["MSE"], "RMSE": eval1["RMSE"],
        "R2": eval1["R2"], "Training Time (s)": time1,
        "Epoch": best_ep1, "Params": count_params(model1),
    }

    # =========================================================================
    # MODEL 2 : DNN + PCA
    # =========================================================================
    print("\n" + "#" * 70)
    print("# MODEL 2 : DNN + PCA")
    print("#" * 70)
    model2 = build_dnn(input_dim=pca_info["n_components"])
    hist2, time2, best_ep2 = train_model(
        model2, data["X_train_pca"], data["y_train_s"],
        data["X_val_pca"], data["y_val_s"],
        checkpoint_path=str(OUTPUT_DIR / "best_dnn_pca.keras"),
    )
    print("\n  [Evaluasi Model 2 - data test, skala Dollar]")
    eval2 = evaluate_model(model2, data["X_test_pca"], data["y_test"],
                           target_scaler)
    plot_loss_curve(hist2, "Model2_PCA")
    plot_residual(data["y_test"], eval2["y_pred"], "Model2_PCA")
    plot_actual_vs_pred(data["y_test"], eval2["y_pred"], "Model2_PCA")
    results["Model 2 (DNN + PCA)"] = {
        "MAE": eval2["MAE"], "MSE": eval2["MSE"], "RMSE": eval2["RMSE"],
        "R2": eval2["R2"], "Training Time (s)": time2,
        "Epoch": best_ep2, "Params": count_params(model2),
    }

    # ---- Analisis PCA (ringkas) ---------------------------------------------
    print("\n" + "=" * 70)
    print("ANALISIS PCA")
    print("=" * 70)
    n_components = pca_info["n_components"]
    info_retained = pca_info["cum_evr"][n_components - 1] * 100
    print(f"Jumlah fitur awal            : {n_features_awal}")
    print(f"Jumlah principal component   : {n_components}")
    print(f"Informasi dipertahankan      : {info_retained:.2f}%")
    print(f"Reduksi dimensi              : "
          f"{n_features_awal} -> {n_components} "
          f"({(1 - n_components / n_features_awal) * 100:.1f}% lebih ringkas)")
    print(f"Waktu training Model 1       : {time1:.1f} detik")
    print(f"Waktu training Model 2 (PCA) : {time2:.1f} detik")

    # ---- Tabel perbandingan --------------------------------------------------
    print("\n" + "=" * 70)
    print("PERBANDINGAN MODEL")
    print("=" * 70)
    comp = pd.DataFrame(results).T
    comp = comp[["MAE", "MSE", "RMSE", "R2", "Training Time (s)",
                 "Epoch", "Params"]]
    comp_display = comp.copy()
    comp_display["MAE"] = comp_display["MAE"].map("{:,.2f}".format)
    comp_display["MSE"] = comp_display["MSE"].map("{:,.0f}".format)
    comp_display["RMSE"] = comp_display["RMSE"].map("{:,.2f}".format)
    comp_display["R2"] = comp_display["R2"].map("{:.4f}".format)
    comp_display["Training Time (s)"] = comp_display["Training Time (s)"].map(
        "{:.1f}".format)
    comp_display["Params"] = comp_display["Params"].map("{:,.0f}".format)
    print(comp_display.to_string())

    # ---- Pemilihan model terbaik (berdasarkan R2) ----------------------------
    best_name = comp["R2"].astype(float).idxmax()
    use_pca = best_name == "Model 2 (DNN + PCA)"
    model_file = "best_dnn_pca.keras" if use_pca else "best_dnn_nopca.keras"
    best_model_obj = model2 if use_pca else model1
    print(f"\n>> MODEL TERBAIK (R2 tertinggi): {best_name}")

    # Simpan tabel perbandingan & metrik untuk laporan
    comp.to_csv(OUTPUT_DIR / "comparison_table.csv")
    with open(OUTPUT_DIR / "results.json", "w") as f:
        json.dump(
            {k: {kk: float(vv) for kk, vv in v.items()}
             for k, v in results.items()},
            f, indent=2,
        )

    weights_file = model_file.replace(".keras", ".weights.h5")
    best_model_obj.save_weights(OUTPUT_DIR / weights_file)

    # ---- Simpan artefak model terbaik (untuk backend/inference) ---------------
    save_artifacts(
        preprocessor, pca, target_scaler, best_name, use_pca, model_file,
        weights_file, n_components if use_pca else None,
    )

    print("\nartefak sudah di folder:", OUTPUT_DIR)
    print("PIPELINE SELESAI")


if __name__ == "__main__":
    main()
