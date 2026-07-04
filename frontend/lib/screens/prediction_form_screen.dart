import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/house_features.dart';
import '../providers/prediction_provider.dart';
import '../widgets/result_bottom_sheet.dart';
import 'history_screen.dart';

class PredictionFormScreen extends StatefulWidget {
  const PredictionFormScreen({super.key});

  @override
  State<PredictionFormScreen> createState() => _PredictionFormScreenState();
}

class _PredictionFormScreenState extends State<PredictionFormScreen> {
  final _formKey = GlobalKey<FormState>();

  final _longitudeCtrl = TextEditingController(text: '-122.23');
  final _latitudeCtrl = TextEditingController(text: '37.88');
  final _ageCtrl = TextEditingController();
  final _totalRoomsCtrl = TextEditingController();
  final _totalBedroomsCtrl = TextEditingController();
  final _populationCtrl = TextEditingController();
  final _householdsCtrl = TextEditingController();
  final _incomeCtrl = TextEditingController();
  String _oceanProximity = kOceanProximityOptions.first;

  @override
  void dispose() {
    _longitudeCtrl.dispose();
    _latitudeCtrl.dispose();
    _ageCtrl.dispose();
    _totalRoomsCtrl.dispose();
    _totalBedroomsCtrl.dispose();
    _populationCtrl.dispose();
    _householdsCtrl.dispose();
    _incomeCtrl.dispose();
    super.dispose();
  }

  String? _requiredPositiveNumber(String? value, {String label = 'Nilai'}) {
    if (value == null || value.trim().isEmpty) return '$label wajib diisi';
    final parsed = double.tryParse(value.trim());
    if (parsed == null) return '$label harus berupa angka';
    if (parsed <= 0) return '$label harus lebih besar dari 0';
    return null;
  }

  String? _validateLongitude(String? value) {
    final parsed = double.tryParse(value?.trim() ?? '');
    if (parsed == null) return 'Longitude harus berupa angka';
    if (parsed < -125 || parsed > -113) {
      return 'Longitude di luar rentang California (-125 s.d -113)';
    }
    return null;
  }

  String? _validateLatitude(String? value) {
    final parsed = double.tryParse(value?.trim() ?? '');
    if (parsed == null) return 'Latitude harus berupa angka';
    if (parsed < 32 || parsed > 43) {
      return 'Latitude di luar rentang California (32 s.d 43)';
    }
    return null;
  }

  String? _validateBedroomsVsRooms(String? value) {
    final basic = _requiredPositiveNumber(value, label: 'total_bedrooms');
    if (basic != null) return basic;
    final bedrooms = double.parse(value!.trim());
    final rooms = double.tryParse(_totalRoomsCtrl.text.trim());
    if (rooms != null && bedrooms > rooms) {
      return 'total_bedrooms tidak boleh lebih besar dari total_rooms';
    }
    return null;
  }

  Future<void> _pickLocationQuick() async {
    // Pilihan cepat lokasi populer di California sebagai alternatif ringan
    // dari integrasi peta penuh. Untuk peta interaktif sesungguhnya, ganti
    // dialog ini dengan google_maps_flutter atau flutter_map + tap handler
    // yang mengembalikan LatLng, lalu isi controller longitude/latitude.
    const presets = {
      'San Francisco Bay Area': (-122.42, 37.77),
      'Los Angeles': (-118.24, 34.05),
      'San Diego': (-117.16, 32.72),
      'Sacramento (Inland)': (-121.49, 38.58),
      'Fresno (Inland)': (-119.77, 36.75),
    };

    final selected = await showDialog<String>(
      context: context,
      builder: (context) => SimpleDialog(
        title: const Text('Pilih Lokasi Cepat'),
        children: presets.keys
            .map((name) => SimpleDialogOption(
                  onPressed: () => Navigator.pop(context, name),
                  child: Text(name),
                ))
            .toList(),
      ),
    );

    if (selected != null) {
      final coords = presets[selected]!;
      setState(() {
        _longitudeCtrl.text = coords.$1.toString();
        _latitudeCtrl.text = coords.$2.toString();
      });
    }
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;

    final features = HouseFeatures(
      longitude: double.parse(_longitudeCtrl.text.trim()),
      latitude: double.parse(_latitudeCtrl.text.trim()),
      housingMedianAge: double.parse(_ageCtrl.text.trim()),
      totalRooms: double.parse(_totalRoomsCtrl.text.trim()),
      totalBedrooms: double.parse(_totalBedroomsCtrl.text.trim()),
      population: double.parse(_populationCtrl.text.trim()),
      households: double.parse(_householdsCtrl.text.trim()),
      medianIncome: double.parse(_incomeCtrl.text.trim()),
      oceanProximity: _oceanProximity,
    );

    final provider = context.read<PredictionProvider>();
    await provider.predict(features);

    if (!mounted) return;

    if (provider.status == PredictionStatus.success &&
        provider.lastPrediction != null) {
      await showPredictionResultSheet(context, provider.lastPrediction!);
    } else if (provider.status == PredictionStatus.error) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(provider.errorMessage ?? 'Terjadi kesalahan.'),
          backgroundColor: Theme.of(context).colorScheme.error,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = context.watch<PredictionProvider>().isLoading;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Prediksi Harga Rumah'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history_rounded),
            tooltip: 'Riwayat Prediksi',
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const HistoryScreen()),
            ),
          ),
        ],
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                padding: const EdgeInsets.all(20),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _HeaderCard(),
                      const SizedBox(height: 20),
                      _sectionLabel('Lokasi'),
                      Row(
                        children: [
                          Expanded(
                            child: TextFormField(
                              controller: _longitudeCtrl,
                              decoration: const InputDecoration(
                                labelText: 'Longitude',
                                prefixIcon: Icon(Icons.explore_outlined),
                              ),
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                      decimal: true, signed: true),
                              validator: _validateLongitude,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextFormField(
                              controller: _latitudeCtrl,
                              decoration: const InputDecoration(
                                labelText: 'Latitude',
                                prefixIcon: Icon(Icons.explore_outlined),
                              ),
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                      decimal: true, signed: true),
                              validator: _validateLatitude,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          onPressed: _pickLocationQuick,
                          icon: const Icon(Icons.map_outlined, size: 18),
                          label: const Text('Pilih Lokasi Cepat'),
                        ),
                      ),
                      const SizedBox(height: 12),
                      _sectionLabel('Karakteristik Properti'),
                      TextFormField(
                        controller: _ageCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Usia median rumah (tahun)',
                          prefixIcon: Icon(Icons.calendar_month_outlined),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (v) =>
                            _requiredPositiveNumber(v, label: 'Usia rumah'),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _totalRoomsCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Total kamar (total_rooms)',
                          prefixIcon: Icon(Icons.meeting_room_outlined),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (v) =>
                            _requiredPositiveNumber(v, label: 'total_rooms'),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _totalBedroomsCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Total kamar tidur (total_bedrooms)',
                          prefixIcon: Icon(Icons.bed_outlined),
                        ),
                        keyboardType: TextInputType.number,
                        validator: _validateBedroomsVsRooms,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _populationCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Populasi sekitar (population)',
                          prefixIcon: Icon(Icons.groups_outlined),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (v) =>
                            _requiredPositiveNumber(v, label: 'population'),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _householdsCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Jumlah rumah tangga (households)',
                          prefixIcon: Icon(Icons.house_siding_outlined),
                        ),
                        keyboardType: TextInputType.number,
                        validator: (v) =>
                            _requiredPositiveNumber(v, label: 'households'),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _incomeCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Median income (puluhan ribu USD, misal 8.3252)',
                          prefixIcon: Icon(Icons.payments_outlined),
                        ),
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        validator: (v) =>
                            _requiredPositiveNumber(v, label: 'median_income'),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        initialValue: _oceanProximity,
                        decoration: const InputDecoration(
                          labelText: 'Kedekatan dengan laut (ocean_proximity)',
                          prefixIcon: Icon(Icons.waves_outlined),
                        ),
                        items: kOceanProximityOptions
                            .map((opt) => DropdownMenuItem(
                                  value: opt,
                                  child: Text(opt),
                                ))
                            .toList(),
                        onChanged: (value) {
                          if (value != null) {
                            setState(() => _oceanProximity = value);
                          }
                        },
                      ),
                      const SizedBox(height: 28),
                      ElevatedButton.icon(
                        onPressed: isLoading ? null : _submit,
                        icon: isLoading
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Icon(Icons.calculate_outlined),
                        label: Text(
                            isLoading ? 'Menghitung...' : 'Prediksi Harga'),
                      ),
                      const SizedBox(height: 12),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _sectionLabel(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 10, top: 4),
        child: Text(
          text,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15),
        ),
      );
}

class _HeaderCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Row(
          children: [
            CircleAvatar(
              radius: 26,
              backgroundColor: theme.colorScheme.primary.withValues(alpha: 0.12),
              child: Icon(Icons.villa_outlined,
                  color: theme.colorScheme.primary, size: 28),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Estimasi Harga Rumah California',
                      style: theme.textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  const SizedBox(height: 4),
                  Text(
                    'Isi data properti di bawah untuk mendapatkan estimasi harga.',
                    style: theme.textTheme.bodySmall
                        ?.copyWith(color: theme.colorScheme.onSurfaceVariant),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
