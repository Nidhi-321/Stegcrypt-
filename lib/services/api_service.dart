// lib/services/api_service.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

/// Simple, opinionated ApiService used by the Flutter UI.
/// - singleton: ApiService.instance
/// - call pattern: await ApiService.instance.get('/users');
/// - returns decoded Map<String, dynamic> on success, or throws on network errors.
class ApiService {
  ApiService._();

  static final ApiService instance = ApiService._();

  /// Change this to your production backend base URL (no trailing slash)
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000', // for Android emulator -> host machine
  );

  String? _authToken;

  /// read-only token accessor (used by SocketService and other consumers)
  String? get token => _authToken;

  /// Set auth token so requests will include Authorization header.
  void setAuthToken(String token) {
    _authToken = token;
  }

  /// Clear the saved token.
  void clearAuthToken() {
    _authToken = null;
  }

  Map<String, String> _defaultHeaders({bool jsonContent = true}) {
    final headers = <String, String>{
      'Accept': 'application/json',
    };
    if (jsonContent) headers['Content-Type'] = 'application/json';
    if (_authToken != null) headers['Authorization'] = 'Bearer $_authToken';
    return headers;
  }

  Uri _buildUri(String path) {
    final normalized = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$baseUrl$normalized');
  }

  Future<Map<String, dynamic>> get(String path, {Map<String, String>? queryParams}) async {
    final uri = _buildUri(path).replace(queryParameters: queryParams);
    final res = await http.get(uri, headers: _defaultHeaders());
    return _decodeResponse(res);
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic>? body, {Map<String, String>? queryParams}) async {
    final uri = _buildUri(path).replace(queryParameters: queryParams);
    final res = await http.post(uri, headers: _defaultHeaders(), body: body == null ? null : jsonEncode(body));
    return _decodeResponse(res);
  }

  Future<Map<String, dynamic>> put(String path, Map<String, dynamic>? body) async {
    final uri = _buildUri(path);
    final res = await http.put(uri, headers: _defaultHeaders(), body: body == null ? null : jsonEncode(body));
    return _decodeResponse(res);
  }

  Future<Map<String, dynamic>> delete(String path) async {
    final uri = _buildUri(path);
    final res = await http.delete(uri, headers: _defaultHeaders());
    return _decodeResponse(res);
  }

  Map<String, dynamic> _decodeResponse(http.Response res) {
    // Try to decode JSON body; if empty, return status + empty body
    final code = res.statusCode;
    if (res.body.isEmpty) {
      return {'statusCode': code, 'body': ''};
    }
    try {
      final decoded = jsonDecode(res.body);
      if (decoded is Map<String, dynamic>) {
        // include status code for callers that expect it
        decoded['statusCode'] = code;
        return decoded;
      }
      // if backend returns list or primitive, wrap
      return {'data': decoded, 'statusCode': code};
    } catch (e) {
      // non-json body
      return {'statusCode': code, 'body': res.body};
    }
  }
}
