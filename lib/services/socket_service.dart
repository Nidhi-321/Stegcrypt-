// lib/services/socket_service.dart
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;

import 'api_service.dart';
import 'auth_service.dart';

/// SocketService adapted to your project:
/// - factory supports SocketService() and SocketService(authService: authService)
/// - exposes `socket` (so UI can access socketSvc.socket)
/// - exposes on/once/off/emit, connect/disconnect, reauthAndReconnect
class SocketService {
  SocketService._internal({AuthService? authService}) {
    _authService = authService;
  }

  static SocketService? _instance;

  factory SocketService({AuthService? authService}) {
    _instance ??= SocketService._internal(authService: authService);
    if (authService != null) _instance!._authService = authService;
    return _instance!;
  }

  AuthService? _authService;

  IO.Socket? socket;
  final List<_BufferedEmit> _buffer = [];

  bool get isConnected => socket != null && socket!.connected;

  /// Connect to server. Optionally override host (useful for testing)
  void connect({String? hostOverride}) {
    if (socket != null && socket!.connected) return;

    var host = hostOverride ?? ApiService.baseUrl; // e.g. http://127.0.0.1:5000/api
    try {
      final uri = Uri.parse(host);
      if (uri.path.isNotEmpty && uri.path != '/') {
        host = host.replaceFirst(uri.path, '');
      }
    } catch (e) {
      if (kDebugMode) debugPrint('SocketService host parse error: $e');
    }

    final token = _authService?.token ?? ApiService().token;

    try {
      socket = IO.io(host, IO.OptionBuilder()
          .setTransports(['websocket', 'polling'])
          .disableAutoConnect()
          .setExtraHeaders({'Authorization': token != null ? 'Bearer $token' : ''})
          .setTimeout(20000)
          .build());

      socket!.on('connect', (_) {
        if (kDebugMode) debugPrint('Socket connected: ${socket!.id}');
        _flushBuffer();
      });

      socket!.on('disconnect', (reason) {
        if (kDebugMode) debugPrint('Socket disconnected: $reason');
      });

      socket!.on('connect_error', (err) {
        if (kDebugMode) debugPrint('Socket connect_error: $err');
      });

      socket!.connect();
    } catch (e) {
      if (kDebugMode) debugPrint('SocketService.connect exception: $e');
    }
  }

  void disconnect() {
    try {
      socket?.disconnect();
      socket = null;
    } catch (e) {
      if (kDebugMode) debugPrint('SocketService.disconnect exception: $e');
    }
  }

  void on(String event, Function(dynamic) handler) {
    socket?.on(event, (data) {
      try {
        handler(data);
      } catch (e) {
        if (kDebugMode) debugPrint('SocketService.on handler error: $e');
      }
    });
  }

  void once(String event, Function(dynamic) handler) {
    socket?.once(event, (data) {
      try {
        handler(data);
      } catch (e) {
        if (kDebugMode) debugPrint('SocketService.once handler error: $e');
      }
    });
  }

  void off(String event) {
    socket?.off(event);
  }

  void emit(String event, dynamic payload, {bool bufferIfDisconnected = true}) {
    if (socket == null || !socket!.connected) {
      if (bufferIfDisconnected) {
        _buffer.add(_BufferedEmit(event, payload));
        if (kDebugMode) debugPrint('SocketService: buffered emit $event');
      } else {
        if (kDebugMode) debugPrint('SocketService: drop emit (not connected) $event');
      }
      return;
    }
    try {
      socket!.emit(event, payload);
    } catch (e) {
      if (kDebugMode) debugPrint('SocketService.emit error: $e');
    }
  }

  void _flushBuffer() {
    if (socket == null || !socket!.connected) return;
    for (final buffered in List<_BufferedEmit>.from(_buffer)) {
      try {
        socket!.emit(buffered.event, buffered.payload);
      } catch (e) {
        if (kDebugMode) debugPrint('SocketService flush emit error: $e');
      }
      _buffer.remove(buffered);
    }
  }

  Future<void> reauthAndReconnect() async {
    disconnect();
    await Future.delayed(const Duration(milliseconds: 200));
    connect();
  }
}

class _BufferedEmit {
  final String event;
  final dynamic payload;
  _BufferedEmit(this.event, this.payload);
}
