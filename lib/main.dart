// lib/main.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'app.dart';

void main() {
  // choose storage implementation; for now we use in-memory.
  final storage = InMemoryStorage();
  final authService = AuthService(storage: storage);

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider<AuthService>.value(value: authService),
      ],
      child: const MyApp(),
    ),
  );
}
