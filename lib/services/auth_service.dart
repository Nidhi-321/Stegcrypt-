// lib/services/auth_service.dart
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'storage_service.dart';
import 'api_service.dart';
import '../models/user.dart';
import '../config.dart';

class AuthService extends ChangeNotifier {
  final StorageService storageService;
  ApiService api;

  bool isLoading = true;
  bool isAuthenticated = false;
  String? token;
  User? user;

  AuthService({required this.storageService}) : api = ApiService() {
    _loadFromStorage();
  }

  Future<void> _loadFromStorage() async {
    token = await storageService.read('access_token');
    final userJson = await storageService.read('user');
    if (token != null && userJson != null) {
      user = User.fromJson(userJson);
      isAuthenticated = true;
      api = ApiService(token: token);
    }
    isLoading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>> login(String username, String password) async {
    final resp = await ApiService().post('/login', {'username': username, 'password': password});
    if (resp.statusCode == 200) {
      final data = jsonDecode(resp.body);
      token = data['access_token'];
      user = User.fromMap(data['user']);
      await storageService.write('access_token', token!);
      await storageService.write('user', jsonEncode(user!.toMap()));
      api = ApiService(token: token);
      isAuthenticated = true;
      notifyListeners();
      return {'ok': true, 'data': data};
    } else {
      return {'ok': false, 'error': resp.body};
    }
  }

  Future<Map<String, dynamic>> register(String username, String password, {String? publicKey}) async {
    final body = {'username': username, 'password': password};
    if (publicKey != null) body['public_key'] = publicKey;
    final resp = await ApiService().post('/register', body);
    if (resp.statusCode == 201) {
      final data = jsonDecode(resp.body);
      token = data['access_token'];
      user = User.fromMap(data['user']);
      await storageService.write('access_token', token!);
      await storageService.write('user', jsonEncode(user!.toMap()));
      api = ApiService(token: token);
      isAuthenticated = true;
      notifyListeners();
      return {'ok': true, 'data': data};
    } else {
      return {'ok': false, 'error': resp.body};
    }
  }

  Future<void> logout() async {
    isAuthenticated = false;
    token = null;
    user = null;
    await storageService.delete('access_token');
    await storageService.delete('user');
    api = ApiService();
    notifyListeners();
  }
}
