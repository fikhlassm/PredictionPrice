# Rumahku Predictor (Flutter)

Aplikasi mobile untuk memprediksi `median_house_value` California dengan
memanggil backend FastAPI yang meng-serve **Model 1: DNN tanpa PCA**.

## Struktur folder

```
flutter_app/
  pubspec.yaml
  lib/
    main.dart
    config/
      api_config.dart          # base URL emulator/device/produksi
    models/
      house_features.dart      # 9 fitur input + daftar ocean_proximity
      prediction_record.dart   # entri riwayat (fitur + hasil + waktu)
    services/
      api_service.dart         # panggilan HTTP ke POST /predict, GET /health
      history_service.dart     # penyimpanan riwayat via shared_preferences
    providers/
      prediction_provider.dart # ChangeNotifier: status, hasil, error, riwayat
    screens/
      prediction_form_screen.dart
      history_screen.dart
    widgets/
      result_bottom_sheet.dart # bottom sheet hasil + formatter mata uang
    theme/
      app_theme.dart           # Material 3, skema biru/hijau
```

## Kenapa Provider, bukan Riverpod?

Untuk aplikasi dengan satu state utama (status prediksi + riwayat) dan alur
data yang relatif sederhana (form -> panggil API -> tampilkan hasil),
`provider` (ChangeNotifier) sudah cukup: setup minimal, tidak perlu code
generation, dan mudah dipahami untuk skripsi/tugas akhir. Riverpod lebih
unggul untuk aplikasi besar dengan banyak provider saling bergantung dan
kebutuhan testing yang kompleks — nilai lebihnya belum terlalu terasa untuk
skala aplikasi ini. Jika aplikasi berkembang (misalnya menambah autentikasi,
multi-model, caching kompleks), migrasi ke Riverpod cukup straightforward
karena konsep dasarnya mirip.

## Instalasi & menjalankan

```bash
flutter pub get
flutter run
```

Pastikan backend FastAPI sudah berjalan (lihat `backend/README.md`) dan
`lib/config/api_config.dart` sudah diarahkan ke target yang benar:

- Emulator Android -> `Environment.androidEmulator` (default, `10.0.2.2`)
- Simulator iOS -> `Environment.iosSimulator`
- HP fisik (WiFi sama) -> `Environment.localNetwork`, isi `localNetworkIp`
  dengan IP lokal komputer Anda
- Produksi -> `Environment.production`, isi `productionUrl`

Atau override langsung tanpa mengubah kode:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

## Alur aplikasi

1. `PredictionFormScreen` menampilkan form 9 fitur dengan validasi lokal
   (semua field wajib, harus angka positif, `total_bedrooms <= total_rooms`,
   `households <= population`, longitude/latitude dalam rentang California).
2. Saat tombol "Prediksi Harga" ditekan, `PredictionProvider.predict()`
   memanggil `ApiService.predictPrice()` (package `http`) ke
   `POST /predict`.
3. Selama request berjalan, tombol menampilkan `CircularProgressIndicator`.
4. Jika sukses: hasil ditampilkan di `showPredictionResultSheet` (bottom
   sheet) dengan format mata uang USD (`$245,600.00` via package `intl`),
   dan otomatis disimpan ke riwayat lokal (`shared_preferences`).
5. Jika gagal (koneksi/API/validasi server): `SnackBar` merah menampilkan
   pesan error yang ramah pengguna, aplikasi tidak crash.
6. `HistoryScreen` (ikon jam di AppBar) menampilkan daftar prediksi
   sebelumnya, bisa dihapus semua lewat ikon tempat sampah.

## Tentang "Pilih di Peta"

Untuk menjaga dependensi tetap ringan (tanpa API key Google Maps), form ini
menyediakan tombol **"Pilih Lokasi Cepat"** yang mengisi longitude/latitude
dari beberapa titik populer di California. Untuk peta interaktif
sesungguhnya, tambahkan `google_maps_flutter` atau `flutter_map` di
`pubspec.yaml`, lalu ganti isi fungsi `_pickLocationQuick()` di
`prediction_form_screen.dart` dengan halaman peta yang mengembalikan
`LatLng` hasil tap pengguna.

## Catatan implementasi

- Validasi input dilakukan dua kali: di Flutter (UX cepat, mencegah request
  sia-sia) dan di backend (source of truth, karena klien tidak bisa
  dipercaya sepenuhnya).
- `ocean_proximity` di dropdown ditulis persis sama dengan kategori pada
  data training (`NEAR BAY`, `<1H OCEAN`, `INLAND`, `NEAR OCEAN`, `ISLAND`)
  agar tidak terjadi mismatch saat one-hot encoding di backend.
- Ikon menggunakan Material Icons bawaan Flutter (`Icons.*`), tidak ada
  aset berlisensi pihak ketiga.
