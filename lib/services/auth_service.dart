// lib/services/auth_service.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'api_service.dart';
import '../models/user.dart';

/// Small storage abstraction so the app can swap implementations.
abstract class StorageService {
  Future<void> write(String key, String value);
  Future<String?> read(String key);
  Future<void> delete(String key);
}

/// In-memory fallback storage (useful for development / tests).
class InMemoryStorage implements StorageService {
  final Map<String, String> _data = {};
  @override
  Future<void> write(String key, String value) async => _data[key] = value;
  @override
  Future<String?> read(String key) async => _data[key];
  @override
  Future<void> delete(String key) async => _data.remove(key);
}

/// AuthService is a ChangeNotifier used by Provider in the app.
/// It holds the 'user' (if any), token and exposes isLoading/isAuthenticated.
class AuthService extends ChangeNotifier {
  final StorageService _storage;
  final ApiService api = ApiService.instance;

  bool _isLoading = false;
  User? _user;
  String? _token;

  static const _tokenKey = 'auth_token';
  static const _userKey = 'auth_user';

  /// Primary constructor. Provide a StorageService (or omit to use in-memory).
  AuthService({StorageService? storage}) : _storage = storage ?? InMemoryStorage() {
    _init();
  }

  // expose getters expected by UI
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _token != null;
  User? get user => _user;
  String? get token => _token;

  Future<void> _init() async {
    _setLoading(true);
    try {
      final saved = await _storage.read(_tokenKey);
      if (saved != null) {
        _token = saved;
        api.setAuthToken(_token!);
        // try to restore saved user
        final ujson = await _storage.read(_userKey);
        if (ujson != null) {
          try {
            final map = jsonDecode(ujson) as Map<String, dynamic>;
            _user = User.fromMap(map);
          } catch (_) {
            // ignore parse errors
          }
        } else {
          // optionally try to fetch /me to populate user metadata
          try {
            final me = await api.get('/me');
            if (me.containsKey('user')) {
              _user = User.fromMap(Map<String, dynamic>.from(me['user']));
              await _storage.write(_userKey, jsonEncode(me['user']));
            }
          } catch (_) {
            // ignore network errors during init
          }
        }
      }
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool v) {
    _isLoading = v;
    notifyListeners();
  }

  /// Attempt login: returns {'ok': true, 'token': '...', 'user': {...}} on success
  Future<Map<String, dynamic>> login(String email, String password) async {
    _setLoading(true);
    try {
      final resp = await api.post('/login', {'email': email, 'password': password});
      final status = resp['statusCode'] ?? 0;
      if (status == 200 || status == 201) {
        // Attempt to extract token from multiple common shapes:
        String? t;
        if (resp.containsKey('token')) t = resp['token']?.toString();
        else if (resp.containsKey('access_token')) t = resp['access_token']?.toString();
        else if (resp.containsKey('data') && resp['data'] is Map && resp['data']['token'] != null) {
          t = resp['data']['token']?.toString();
        }

        if (t != null) {
          _token = t;
          api.setAuthToken(t);
          await _storage.write(_tokenKey, t);

          // user extraction
          if (resp.containsKey('user')) {
            _user = User.fromMap(Map<String, dynamic>.from(resp['user']));
            await _storage.write(_userKey, jsonEncode(resp['user']));
          } else if (resp.containsKey('data') && resp['data'] is Map && resp['data']['user'] != null) {
            _user = User.fromMap(Map<String, dynamic>.from(resp['data']['user']));
            await _storage.write(_userKey, jsonEncode(resp['data']['user']));
          } else {
            // optional: fetch /me
            try {
              final me = await api.get('/me');
              if (me.containsKey('user')) {
                _user = User.fromMap(Map<String, dynamic>.from(me['user']));
                await _storage.write(_userKey, jsonEncode(me['user']));
              }
            } catch (_) {}
          }

          notifyListeners();
          return {'ok': true, 'token': t, 'user': _user?.toMap()};
        } else {
          return {'ok': false, 'error': 'No token returned from server', 'raw': resp};
        }
      } else {
        final err = resp['body'] ?? resp['error'] ?? resp['message'] ?? 'Login failed';
        return {'ok': false, 'error': err};
      }
    } catch (e) {
      return {'ok': false, 'error': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  /// Register a new user. Returns a map similar to login's return.
  Future<Map<String, dynamic>> register(String name, String email, String password) async {
    _setLoading(true);
    try {
      final resp = await api.post('/register', {'name': name, 'email': email, 'password': password});
      final status = resp['statusCode'] ?? 0;
      if (status == 201 || status == 200) {
        // if token returned, store it
        String? t;
        if (resp.containsKey('token')) t = resp['token']?.toString();
        else if (resp.containsKey('data') && resp['data'] is Map && resp['data']['token'] != null) {
          t = resp['data']['token']?.toString();
        }

        if (t != null) {
          _token = t;
          api.setAuthToken(t);
          await _storage.write(_tokenKey, t);

          if (resp.containsKey('user')) {
            _user = User.fromMap(Map<String, dynamic>.from(resp['user']));
            await _storage.write(_userKey, jsonEncode(resp['user']));
          }

          notifyListeners();
          return {'ok': true, 'token': t, 'user': _user?.toMap()};
        } else {
          return {'ok': true, 'raw': resp};
        }
      } else {
        return {'ok': false, 'error': resp['body'] ?? resp['error'] ?? resp['message'] ?? 'Register failed'};
      }
    } catch (e) {
      return {'ok': false, 'error': e.toString()};
    } finally {
      _setLoading(false);
    }
  }

  /// Clear auth state
  Future<void> logout() async {
    _token = null;
    _user = null;
    api.clearAuthToken();
    await _storage.delete(_tokenKey);
    await _storage.delete(_userKey);
    notifyListeners();
  }
}
