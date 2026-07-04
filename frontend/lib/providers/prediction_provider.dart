import 'package:flutter/foundation.dart';

import '../models/house_features.dart';
import '../models/prediction_record.dart';
import '../services/api_service.dart';
import '../services/history_service.dart';

enum PredictionStatus { idle, loading, success, error }

/// Mengelola state prediksi: status loading/sukses/error, hasil, dan
/// riwayat. Memakai Provider (ChangeNotifier) -- lihat README Flutter
/// untuk alasan pemilihan dibanding Riverpod.
class PredictionProvider extends ChangeNotifier {
  final ApiService _apiService;
  final HistoryService _historyService;

  PredictionProvider({
    ApiService? apiService,
    HistoryService? historyService,
  })  : _apiService = apiService ?? ApiService(),
        _historyService = historyService ?? HistoryService();

  PredictionStatus status = PredictionStatus.idle;
  double? lastPrediction;
  String? errorMessage;
  List<PredictionRecord> history = [];

  bool get isLoading => status == PredictionStatus.loading;

  Future<void> loadHistory() async {
    history = await _historyService.loadHistory();
    notifyListeners();
  }

  Future<void> predict(HouseFeatures features) async {
    status = PredictionStatus.loading;
    errorMessage = null;
    notifyListeners();

    try {
      final price = await _apiService.predictPrice(features);
      lastPrediction = price;
      status = PredictionStatus.success;

      final record = PredictionRecord(
        features: features,
        predictedPrice: price,
        timestamp: DateTime.now(),
      );
      await _historyService.addRecord(record);
      history.insert(0, record);
    } on ApiException catch (e) {
      status = PredictionStatus.error;
      errorMessage = e.message;
    } catch (e) {
      status = PredictionStatus.error;
      errorMessage = 'Terjadi kesalahan tak terduga: $e';
    } finally {
      notifyListeners();
    }
  }

  Future<void> clearHistory() async {
    await _historyService.clearHistory();
    history = [];
    notifyListeners();
  }

  void resetStatus() {
    status = PredictionStatus.idle;
    errorMessage = null;
    notifyListeners();
  }
}
