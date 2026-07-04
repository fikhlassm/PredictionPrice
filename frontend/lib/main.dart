import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/prediction_provider.dart';
import 'screens/prediction_form_screen.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const RumahkuApp());
}

class RumahkuApp extends StatelessWidget {
  const RumahkuApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => PredictionProvider()..loadHistory(),
        ),
      ],
      child: MaterialApp(
        title: 'Prediksi Harga Rumah',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.light(),
        home: const PredictionFormScreen(),
      ),
    );
  }
}
