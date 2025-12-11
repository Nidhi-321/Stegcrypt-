import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:mime/mime.dart';
import 'package:http_parser/http_parser.dart';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}

class ApiService {
  ApiService._();
  static final ApiService instance = ApiService._();

  // TODO: set this to your production backend base URL (https://api.example.com)
  final String baseUrl = const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:5000');

  Map<String, String> _defaultHeaders() => {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };

  Future<Map<String, dynamic>> _handleResponse(http.Response res) async {
    final status = res.statusCode;
    if (res.body.isEmpty) {
      if (status >= 200 && status < 300) return {};
      throw ApiException('Empty response with status $status');
    }

    final dynamic decoded = json.decode(res.body);
    if (status >= 200 && status < 300) {
      if (decoded is Map<String, dynamic>) return decoded;
      return {'data': decoded};
    } else {
      final message = decoded is Map && decoded['message'] != null
          ? decoded['message'].toString()
          : 'API error (status $status)';
      throw ApiException(message);
    }
  }

  Future<Map<String, dynamic>> register(String name, String email, String password) async {
    final uri = Uri.parse('$baseUrl/register');
    final body = json.encode({'name': name, 'email': email, 'password': password});
    final res = await http.post(uri, headers: _defaultHeaders(), body: body).timeout(const Duration(seconds: 30));
    return _handleResponse(res);
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final uri = Uri.parse('$baseUrl/login');
    final body = json.encode({'email': email, 'password': password});
    final res = await http.post(uri, headers: _defaultHeaders(), body: body).timeout(const Duration(seconds: 30));
    return _handleResponse(res);
  }

  Future<Map<String, dynamic>> generateKeyPair() async {
    final uri = Uri.parse('$baseUrl/generate_keypair');
    final res = await http.get(uri, headers: _defaultHeaders()).timeout(const Duration(seconds: 30));
    return _handleResponse(res);
  }

  Future<Map<String, dynamic>> encryptMessage(String plaintext, String recipientPublicKey) async {
    final uri = Uri.parse('$baseUrl/encrypt');
    final body = json.encode({'message': plaintext, 'recipient_public_key': recipientPublicKey});
    final res = await http.post(uri, headers: _defaultHeaders(), body: body).timeout(const Duration(seconds: 30));
    return _handleResponse(res);
  }

  Future<Map<String, dynamic>> decryptMessage(String ciphertext, String privateKey) async {
    final uri = Uri.parse('$baseUrl/decrypt');
    final body = json.encode({'ciphertext': ciphertext, 'private_key': privateKey});
    final res = await http.post(uri, headers: _defaultHeaders(), body: body).timeout(const Duration(seconds: 30));
    return _handleResponse(res);
  }

  /// Uploads an image file and embeds `payload` into it via steganography endpoint.
  /// Returns JSON with embedded image URL or bytes (depending on backend).
  Future<Map<String, dynamic>> embedMessage(File imageFile, String payload, {String? token}) async {
    final uri = Uri.parse('$baseUrl/embed');
    final request = http.MultipartRequest('POST', uri);
    if (token != null) request.headers['Authorization'] = 'Bearer $token';

    final mimeType = lookupMimeType(imageFile.path) ?? 'application/octet-stream';
    final parts = mimeType.split('/');
    final fileStream = http.ByteStream(imageFile.openRead());
    final length = await imageFile.length();

    final multipartFile = http.MultipartFile(
      'image',
      fileStream,
      length,
      filename: imageFile.path.split(Platform.pathSeparator).last,
      contentType: MediaType(parts[0], parts[1]),
    );
    request.files.add(multipartFile);
    request.fields['payload'] = payload;

    final streamed = await request.send().timeout(const Duration(seconds: 60));
    final response = await http.Response.fromStream(streamed);
    return _handleResponse(response);
  }

  /// Uploads an image to extract a hidden payload.
  Future<Map<String, dynamic>> extractMessage(File imageFile, {String? token}) async {
    final uri = Uri.parse('$baseUrl/extract');
    final request = http.MultipartRequest('POST', uri);
    if (token != null) request.headers['Authorization'] = 'Bearer $token';

    final mimeType = lookupMimeType(imageFile.path) ?? 'application/octet-stream';
    final parts = mimeType.split('/');
    final fileStream = http.ByteStream(imageFile.openRead());
    final length = await imageFile.length();

    final multipartFile = http.MultipartFile(
      'image',
      fileStream,
      length,
      filename: imageFile.path.split(Platform.pathSeparator).last,
      contentType: MediaType(parts[0], parts[1]),
    );
    request.files.add(multipartFile);

    final streamed = await request.send().timeout(const Duration(seconds: 60));
    final response = await http.Response.fromStream(streamed);
    return _handleResponse(response);
  }
}
