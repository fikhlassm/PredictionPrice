import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import '../models/house_features.dart';

/// Exception khusus agar UI bisa menampilkan pesan yang ramah pengguna.
class ApiException implements Exception {
  final String message;
  ApiException(this.message);

  @override
  String toString() => message;
}

class ApiService {
  Future<double> predictPrice(HouseFeatures features) async {
    final uri = Uri.parse(ApiConfig.predictEndpoint);

    http.Response response;
    try {
      response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(features.toJson()),
          )
          .timeout(ApiConfig.requestTimeout);
    } on SocketException {
      throw ApiException(
        'Tidak bisa terhubung ke server. Pastikan backend berjalan dan '
        'perangkat terhubung ke jaringan yang sama.',
      );
    } on HttpException {
      throw ApiException('Terjadi masalah komunikasi dengan server.');
    } on FormatException {
      throw ApiException('Format respons server tidak valid.');
    } catch (e) {
      throw ApiException('Waktu koneksi habis atau terjadi kesalahan: $e');
    }

    final Map<String, dynamic> body = _safeDecode(response.body);

    if (response.statusCode == 200) {
      final price = body['predicted_price'];
      if (price is num) return price.toDouble();
      throw ApiException('Respons server tidak sesuai format yang diharapkan.');
    }

    if (response.statusCode == 400) {
      throw ApiException(_extractDetail(body, fallback: 'Input tidak valid.'));
    }

    if (response.statusCode >= 500) {
      throw ApiException(
        _extractDetail(body, fallback: 'Terjadi kesalahan pada server.'),
      );
    }

    throw ApiException('Terjadi kesalahan tak terduga (${response.statusCode}).');
  }

  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse(ApiConfig.healthEndpoint);
      final response = await http.get(uri).timeout(ApiConfig.requestTimeout);
      if (response.statusCode != 200) return false;
      final body = _safeDecode(response.body);
      return body['model_loaded'] == true;
    } catch (_) {
      return false;
    }
  }

  Map<String, dynamic> _safeDecode(String source) {
    try {
      final decoded = jsonDecode(source);
      if (decoded is Map<String, dynamic>) return decoded;
      return {};
    } catch (_) {
      return {};
    }
  }

  String _extractDetail(Map<String, dynamic> body, {required String fallback}) {
    final detail = body['detail'];
    if (detail is String) return detail;
    if (detail is List && detail.isNotEmpty) {
      // Pydantic validation error list
      return detail
          .map((e) => e is Map && e['msg'] != null ? e['msg'].toString() : e.toString())
          .join('\n');
    }
    return fallback;
  }
}
