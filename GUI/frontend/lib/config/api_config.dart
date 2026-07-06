/// Konfigurasi environment untuk base URL API backend.
///
/// Ganti [Environment.current] di bawah untuk berpindah target:
/// - androidEmulator : http://10.0.2.2:8000        (emulator Android SAJA)
/// - iosSimulator    : http://127.0.0.1:8000        (simulator iOS, Chrome web,
///                                                    Windows/macOS/Linux desktop
///                                                    -- default project ini)
/// - localNetwork    : http://<IP-LOKAL-PC>:8000    (HP fisik, WiFi sama)
/// - production      : URL server hasil deploy (Railway/Render/dll)
///
/// Alternatif: jalankan dengan --dart-define, misal:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
library;

enum Environment { androidEmulator, iosSimulator, localNetwork, production }

class ApiConfig {
  ApiConfig._();

  /// Pilih environment aktif secara manual di sini saat development.
  /// Untuk Chrome/Windows desktop (flutter run -d chrome / -d windows),
  /// backend lokal diakses lewat 127.0.0.1, sama seperti iosSimulator.
  /// Ganti ke Environment.androidEmulator HANYA saat run di emulator Android.
  static const Environment current = Environment.iosSimulator;

  /// Isi dengan IP lokal PC Anda saat testing di HP fisik.
  static const String localNetworkIp = 'http://192.168.1.10:8000';

  /// Isi dengan URL hasil deploy (Railway/Render/VPS) untuk produksi.
  static const String productionUrl = 'https://your-app-name.up.railway.app';

  static String get baseUrl {
    // Prioritaskan nilai dari --dart-define jika disediakan.
    const fromDefine = String.fromEnvironment('API_BASE_URL');
    if (fromDefine.isNotEmpty) return fromDefine;

    switch (current) {
      case Environment.androidEmulator:
        return 'http://10.0.2.2:8000';
      case Environment.iosSimulator:
        return 'http://127.0.0.1:8000';
      case Environment.localNetwork:
        return localNetworkIp;
      case Environment.production:
        return productionUrl;
    }
  }

  static String get predictEndpoint => '$baseUrl/predict';
  static String get healthEndpoint => '$baseUrl/health';

  /// Timeout untuk request HTTP.
  static const Duration requestTimeout = Duration(seconds: 15);
}