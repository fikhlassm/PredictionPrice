import 'house_features.dart';

/// Satu entri riwayat prediksi: fitur input + hasil + waktu prediksi.
class PredictionRecord {
  final HouseFeatures features;
  final double predictedPrice;
  final DateTime timestamp;

  const PredictionRecord({
    required this.features,
    required this.predictedPrice,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
        'features': features.toJson(),
        'predicted_price': predictedPrice,
        'timestamp': timestamp.toIso8601String(),
      };

  factory PredictionRecord.fromJson(Map<String, dynamic> json) =>
      PredictionRecord(
        features:
            HouseFeatures.fromJson(json['features'] as Map<String, dynamic>),
        predictedPrice: (json['predicted_price'] as num).toDouble(),
        timestamp: DateTime.parse(json['timestamp'] as String),
      );
}
