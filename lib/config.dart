// lib/config.dart
class Config {
  // Update this to your backend public URL (include /api if you host API under /api)
  // For local dev with backend docker-compose exposing port 5000:
  // web: http://localhost:5000/api
  // mobile: use network IP of development machine, e.g. http://192.168.1.10:5000/api
  static const String API_BASE_URL = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:5000/api');
}
