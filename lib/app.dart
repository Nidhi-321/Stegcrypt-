// lib/app.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_service.dart';
import 'screens/login_screen.dart';
import 'screens/users_screen.dart';

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'StegCrypt+',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const RootRouter(),
    );
  }
}

class RootRouter extends StatelessWidget {
  const RootRouter({super.key});
  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context);

    if (auth.isLoading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    } else if (auth.isAuthenticated) {
      return const UsersScreen();
    } else {
      return LoginScreen(
        onLoginSuccess: () {
          // rebuild root when login completes; auth ChangeNotifier will notify listeners
          (Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const UsersScreen())));
        },
      );
    }
  }
}
