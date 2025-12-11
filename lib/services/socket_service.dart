// lib/services/socket_service.dart
/// Minimal stub so ChatScreen and other code compile.
/// Replace with your real socket implementation (socket_io_client or websockets).
typedef SocketCallback = void Function(dynamic data);

class SocketService {
  dynamic socket;
  final Map<String, List<SocketCallback>> _handlers = {};

  void connect({String? host}) {
    // no-op stub: in real app connect to server and set socket
    socket = Object();
  }

  void on(String event, SocketCallback cb) {
    _handlers.putIfAbsent(event, () => []).add(cb);
  }

  void emit(String event, dynamic data) {
    // call handlers locally (for testing)
    final list = _handlers[event];
    if (list != null) {
      for (final cb in list) cb(data);
    }
  }
}
