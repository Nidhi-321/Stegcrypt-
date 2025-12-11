// lib/services/api_service.dart
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

/// ApiService adapted to your project:
/// - Singleton factory supports ApiService() and ApiService(token: token)
/// - Exposes get/post/put/delete/uploadFile returning http.Response / StreamedResponse
/// - Public static baseUrl with safe default; use setBaseUrl() to override at runtime
class ApiService {
  ApiService._internal({String? token}) {
    _token = token;
  }

  static final ApiService _instance = ApiService._internal();

  /// Factory - matches existing calls in your code that call ApiService() or ApiService(token: token)
  factory ApiService({String? token}) {
    if (token != null && token.isNotEmpty) {
      _instance._token = token;
    }
    return _instance;
  }

  /// Public baseUrl (so legacy code can use ApiService.baseUrl). Default to localhost.
  static String baseUrl = 'http://127.0.0.1:5000/api';

  /// Use this to override base URL at runtime (call from main or config loader)
  static void setBaseUrl(String url) {
    baseUrl = url;
  }

  final http.Client _client = http.Client();
  String? _token;

  static const String _prefsTokenKey = 'access_token';

  String? get token => _token;

  void setToken(String? token) {
    _token = token;
  }

  Future<void> persistToken() async {
    if (_token == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsTokenKey, _token!);
  }

  Future<void> loadPersistedToken() async {
    final prefs = await SharedPreferences.getInstance();
    final t = prefs.getString(_prefsTokenKey);
    if (t != null && t.isNotEmpty) {
      _token = t;
    }
  }

  Map<String, String> _defaultHeaders({bool json = true}) {
    final headers = <String, String>{};
    if (json) headers['Content-Type'] = 'application/json';
    headers['Accept'] = 'application/json';
    if (_token != null && _token!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  Uri _uri(String path, [Map<String, dynamic>? queryParams]) {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      final u = Uri.parse(path);
      if (queryParams == null) return u;
      return u.replace(queryParameters: queryParams.map((k, v) => MapEntry(k, v.toString())));
    }

    final base = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final p = path.startsWith('/') ? path : '/$path';
    final full = base + p;
    final u = Uri.parse(full);
    if (queryParams == null || queryParams.isEmpty) return u;
    return u.replace(queryParameters: queryParams.map((k, v) => MapEntry(k, v.toString())));
  }

  Future<http.Response> get(String path, {Map<String, dynamic>? params, Map<String, String>? headers, Duration? timeout}) async {
    final uri = _uri(path, params);
    final h = {..._defaultHeaders(), if (headers != null) ...headers};
    try {
      final resp = await _client.get(uri, headers: h).timeout(timeout ?? const Duration(seconds: 15));
      return resp;
    } on SocketException catch (e) {
      if (kDebugMode) debugPrint('ApiService GET network error: $e');
      rethrow;
    } on TimeoutException catch (e) {
      if (kDebugMode) debugPrint('ApiService GET timeout: $e');
      rethrow;
    }
  }

  Future<http.Response> post(String path, Map<String, dynamic>? body, {Map<String, String>? headers, Duration? timeout}) async {
    final uri = _uri(path);
    final h = {..._defaultHeaders(), if (headers != null) ...headers};
    final payload = (body == null) ? null : jsonEncode(body);
    try {
      final resp = await _client.post(uri, headers: h, body: payload).timeout(timeout ?? const Duration(seconds: 15));
      return resp;
    } on SocketException catch (e) {
      if (kDebugMode) debugPrint('ApiService POST network error: $e');
      rethrow;
    } on TimeoutException catch (e) {
      if (kDebugMode) debugPrint('ApiService POST timeout: $e');
      rethrow;
    }
  }

  Future<http.Response> put(String path, Map<String, dynamic>? body, {Map<String, String>? headers, Duration? timeout}) async {
    final uri = _uri(path);
    final h = {..._defaultHeaders(), if (headers != null) ...headers};
    final payload = (body == null) ? null : jsonEncode(body);
    try {
      final resp = await _client.put(uri, headers: h, body: payload).timeout(timeout ?? const Duration(seconds: 15));
      return resp;
    } on SocketException catch (e) {
      if (kDebugMode) debugPrint('ApiService PUT network error: $e');
      rethrow;
    } on TimeoutException catch (e) {
      if (kDebugMode) debugPrint('ApiService PUT timeout: $e');
      rethrow;
    }
  }

  Future<http.Response> delete(String path, {Map<String, dynamic>? body, Map<String, String>? headers, Duration? timeout}) async {
    final uri = _uri(path);
    final h = {..._defaultHeaders(), if (headers != null) ...headers};
    final payload = (body == null) ? null : jsonEncode(body);
    try {
      final resp = await _client.delete(uri, headers: h, body: payload).timeout(timeout ?? const Duration(seconds: 15));
      return resp;
    } on SocketException catch (e) {
      if (kDebugMode) debugPrint('ApiService DELETE network error: $e');
      rethrow;
    } on TimeoutException catch (e) {
      if (kDebugMode) debugPrint('ApiService DELETE timeout: $e');
      rethrow;
    }
  }

  Future<http.StreamedResponse> uploadFile(
    String path, {
    required String filePath,
    required String fieldName,
    Map<String, String>? fields,
    Map<String, String>? extraHeaders,
    Duration? timeout,
  }) async {
    final uri = _uri(path);
    final request = http.MultipartRequest('POST', uri);
    final headers = {..._defaultHeaders(json: false), if (extraHeaders != null) ...extraHeaders};
    request.headers.addAll(headers);

    if (fields != null) request.fields.addAll(fields);

    final multipartFile = await http.MultipartFile.fromPath(fieldName, filePath);
    request.files.add(multipartFile);

    try {
      final streamed = await _client.send(request).timeout(timeout ?? const Duration(seconds: 30));
      return streamed;
    } on SocketException catch (e) {
      if (kDebugMode) debugPrint('ApiService uploadFile network error: $e');
      rethrow;
    } on TimeoutException catch (e) {
      if (kDebugMode) debugPrint('ApiService uploadFile timeout: $e');
      rethrow;
    }
  }

  void dispose() {
    _client.close();
  }
}
