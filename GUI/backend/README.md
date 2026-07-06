# Backend API - Prediksi Harga Rumah California

API FastAPI yang meng-serve **Model 1: DNN tanpa PCA** untuk aplikasi Flutter.

## 1. Persiapan folder

```
backend/
  main.py
  schemas.py
  requirements.txt
  outputs/                     <-- salin dari hasil script training
    best_dnn_nopca.keras
    preprocessor.pkl
    y_scaler.pkl
    meta.json
```

Salin folder `outputs/` yang dihasilkan script training (khususnya 4 file
di atas) ke dalam folder `backend/outputs/`.

## 2. Instalasi

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Menjalankan server (lokal)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Dokumentasi interaktif otomatis: `http://127.0.0.1:8000/docs`
- Cek kesehatan server: `GET http://127.0.0.1:8000/health`
- Prediksi: `POST http://127.0.0.1:8000/predict`

Contoh body request:

```json
{
  "longitude": -122.23,
  "latitude": 37.88,
  "housing_median_age": 41,
  "total_rooms": 880,
  "total_bedrooms": 129,
  "population": 322,
  "households": 126,
  "median_income": 8.3252,
  "ocean_proximity": "NEAR BAY"
}
```

## 4. Mengakses dari HP / emulator

`--host 0.0.0.0` membuat server bisa diakses dari perangkat lain di
jaringan yang sama.

| Klien                          | Base URL                              |
|---------------------------------|----------------------------------------|
| Android Emulator                | `http://10.0.2.2:8000`                |
| iOS Simulator                   | `http://127.0.0.1:8000` atau `http://localhost:8000` |
| HP fisik (WiFi sama dengan PC)  | `http://<IP-LOKAL-PC>:8000` (misal `http://192.168.1.10:8000`) |

Cari IP lokal PC dengan `ipconfig` (Windows) atau `ifconfig` / `ip addr`
(Mac/Linux). Pastikan firewall mengizinkan port 8000.

## 5. Deploy sederhana (opsional, agar bisa diakses tanpa PC menyala)

### Opsi A - Railway / Render
1. Push folder `backend/` (termasuk `outputs/`) ke repo GitHub.
2. Buat service baru di Railway/Render, hubungkan ke repo.
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Setelah deploy, gunakan URL publik yang diberikan (misal
   `https://xxxx.up.railway.app`) sebagai base URL produksi di Flutter.

Catatan: model TensorFlow bisa membuat image build cukup besar; pastikan
plan hosting mendukung ukuran tersebut, atau pertimbangkan mengonversi
model ke TensorFlow Lite jika ingin ukuran lebih kecil.

### Opsi B - Local network only (untuk demo/skripsi)
Cukup jalankan `uvicorn main:app --host 0.0.0.0 --port 8000` di laptop,
pastikan HP & laptop terhubung ke WiFi yang sama, lalu isi base URL
Flutter dengan IP lokal laptop seperti pada tabel di atas.

## 6. Validasi & error handling

- Body request divalidasi otomatis oleh Pydantic (`schemas.py`):
  tipe data, rentang nilai wajar (longitude/latitude California,
  income > 0, dll), `ocean_proximity` harus salah satu dari 5 kategori,
  serta `total_bedrooms <= total_rooms`.
- Input tidak valid -> HTTP 400 dengan detail error dalam JSON.
- Error internal (model gagal load/predict) -> HTTP 500 dengan pesan JSON.
