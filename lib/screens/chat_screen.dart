// lib/screens/chat_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/user.dart';
import '../models/message.dart';
import '../services/auth_service.dart';
import '../services/socket_service.dart';
import '../services/api_service.dart';
import '../widgets/message_bubble.dart';

class ChatScreen extends StatefulWidget {
  final User otherUser;
  const ChatScreen({required this.otherUser, super.key});
  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _textC = TextEditingController();
  List<MessageModel> messages = [];
  bool loading = true;
  late AuthService auth;
  late SocketService socketSvc;

  @override
  void initState() {
    super.initState();
    auth = Provider.of<AuthService>(context, listen: false);
    socketSvc = Provider.of<SocketService>(context, listen: false);
    _loadMessages();
    // connect socket if not connected
    if (socketSvc.socket == null) {
      socketSvc.connect();
    }
    socketSvc.on('new_message', (data) {
      // data expected to be message map
      try {
        setState(() => messages.add(MessageModel.fromMap(Map<String, dynamic>.from(data))));
      } catch (_) {}
    });
  }

  @override
  void dispose() {
    _textC.dispose();
    super.dispose();
  }

  Future<void> _loadMessages() async {
    setState(() {
      loading = true;
    });

    try {
      final r = await auth.api.get('/messages/${widget.otherUser.id}');
      // r is a Map<String,dynamic>; backend might return {'messages': [...] } or {'data': [...]}
      dynamic raw;
      if (r.containsKey('messages')) raw = r['messages'];
      else if (r.containsKey('data')) raw = r['data'];
      else {
        raw = r.values.isNotEmpty && r.values.first is List ? r.values.first : null;
      }

      if (raw is List) {
        final parsed = raw.map((m) {
          if (m is Map<String, dynamic>) return MessageModel.fromMap(m);
          if (m is String) {
            try {
              final dec = jsonDecode(m);
              return MessageModel.fromMap(Map<String, dynamic>.from(dec));
            } catch (_) {
              return null;
            }
          }
          return null;
        }).whereType<MessageModel>().toList();

        setState(() => messages = parsed);
      } else {
        // no messages or unexpected shape: keep empty list
      }
    } catch (e) {
      // silent or set an error state if you prefer
      // ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to load messages: $e')));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _send() async {
    final text = _textC.text.trim();
    if (text.isEmpty) return;
    final payload = {'receiver_id': widget.otherUser.id, 'ciphertext': text};

    try {
      final r = await auth.api.post('/send_message', payload);
      // backend may return {'message': {...}} or {'data': {'message': {...}}}
      Map<String, dynamic>? msg;
      if (r.containsKey('message') && r['message'] is Map<String, dynamic>) {
        msg = Map<String, dynamic>.from(r['message']);
      } else if (r.containsKey('data') && r['data'] is Map && r['data']['message'] is Map) {
        msg = Map<String, dynamic>.from(r['data']['message']);
      } else if (r.values.isNotEmpty && r.values.first is Map && (r.values.first as Map).containsKey('message')) {
        final v = r.values.first as Map;
        msg = Map<String, dynamic>.from(v['message']);
      }

      if (msg != null) {
        setState(() => messages.add(MessageModel.fromMap(msg!)));
        _textC.clear();
      } else {
        // maybe backend returned the message list or success code; attempt to reload
        await _loadMessages();
        _textC.clear();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to send: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = (auth as dynamic).user; // may be null if AuthService doesn't expose user
    return Scaffold(
      appBar: AppBar(title: Text(widget.otherUser.username)),
      body: Column(
        children: [
          Expanded(
            child: loading
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    itemCount: messages.length,
                    itemBuilder: (_, i) {
                      final m = messages[i];
                      final isMe = (me != null && m.senderId == me.id);
                      return MessageBubble(message: m, isMe: isMe);
                    },
                  ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(children: [
              Expanded(child: TextField(controller: _textC, decoration: const InputDecoration(hintText: 'Type ciphertext...'))),
              const SizedBox(width: 8),
              ElevatedButton(onPressed: _send, child: const Text('Send'))
            ]),
          )
        ],
      ),
    );
  }
}
