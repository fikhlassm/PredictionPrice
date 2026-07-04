import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/prediction_record.dart';

/// Menyimpan riwayat prediksi di local storage (shared_preferences),
/// disimpan sebagai list JSON string. Riwayat dibatasi 50 entri terbaru
/// agar penyimpanan tidak membengkak.
class HistoryService {
  static const _key = 'prediction_history';
  static const _maxEntries = 50;

  Future<List<PredictionRecord>> loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_key) ?? [];
    return raw
        .map((s) {
          try {
            return PredictionRecord.fromJson(
                jsonDecode(s) as Map<String, dynamic>);
          } catch (_) {
            return null;
          }
        })
        .whereType<PredictionRecord>()
        .toList()
      ..sort((a, b) => b.timestamp.compareTo(a.timestamp));
  }

  Future<void> addRecord(PredictionRecord record) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getStringList(_key) ?? [];
    raw.insert(0, jsonEncode(record.toJson()));
    final trimmed = raw.take(_maxEntries).toList();
    await prefs.setStringList(_key, trimmed);
  }

  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
