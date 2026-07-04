/// 5 kategori ocean_proximity persis seperti pada data training.
/// Urutan & penulisan HARUS sama dengan yang dipakai backend/model.
const List<String> kOceanProximityOptions = [
  'NEAR BAY',
  '<1H OCEAN',
  'INLAND',
  'NEAR OCEAN',
  'ISLAND',
];

/// Representasi 9 fitur mentah yang dibutuhkan model untuk prediksi.
class HouseFeatures {
  final double longitude;
  final double latitude;
  final double housingMedianAge;
  final double totalRooms;
  final double totalBedrooms;
  final double population;
  final double households;
  final double medianIncome;
  final String oceanProximity;

  const HouseFeatures({
    required this.longitude,
    required this.latitude,
    required this.housingMedianAge,
    required this.totalRooms,
    required this.totalBedrooms,
    required this.population,
    required this.households,
    required this.medianIncome,
    required this.oceanProximity,
  });

  Map<String, dynamic> toJson() => {
        'longitude': longitude,
        'latitude': latitude,
        'housing_median_age': housingMedianAge,
        'total_rooms': totalRooms,
        'total_bedrooms': totalBedrooms,
        'population': population,
        'households': households,
        'median_income': medianIncome,
        'ocean_proximity': oceanProximity,
      };

  factory HouseFeatures.fromJson(Map<String, dynamic> json) => HouseFeatures(
        longitude: (json['longitude'] as num).toDouble(),
        latitude: (json['latitude'] as num).toDouble(),
        housingMedianAge: (json['housing_median_age'] as num).toDouble(),
        totalRooms: (json['total_rooms'] as num).toDouble(),
        totalBedrooms: (json['total_bedrooms'] as num).toDouble(),
        population: (json['population'] as num).toDouble(),
        households: (json['households'] as num).toDouble(),
        medianIncome: (json['median_income'] as num).toDouble(),
        oceanProximity: json['ocean_proximity'] as String,
      );
}
