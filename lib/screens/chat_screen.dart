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
    if (socketSvc.socket == null) socketSvc.connect();
    socketSvc.on('new_message', (data) {
      // data is message map
      setState(() => messages.add(MessageModel.fromMap(data)));
    });
  }

  Future<void> _loadMessages() async {
    setState((){ loading = true; });
    final r = await auth.api.get('/messages/${widget.otherUser.id}');
    if (r.statusCode == 200) {
      final List<dynamic> list = jsonDecode(r.body);
      setState(() => messages = list.map((m) => MessageModel.fromMap(m)).toList());
    }
    setState((){ loading = false; });
  }

  Future<void> _send() async {
    final text = _textC.text.trim();
    if (text.isEmpty) return;
    // TODO: Implement client-side encryption here: use crypto_stub.dart (or pointycastle)
    final payload = {'receiver_id': widget.otherUser.id, 'ciphertext': text};
    final r = await auth.api.post('/send_message', payload);
    if (r.statusCode == 201) {
      final data = jsonDecode(r.body);
      setState(() => messages.add(MessageModel.fromMap(data['message'])));
      _textC.clear();
    } else {
      // handle error
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Failed to send')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final me = auth.user!;
    return Scaffold(
      appBar: AppBar(title: Text(widget.otherUser.username)),
      body: Column(
        children: [
          Expanded(
            child: loading ? const Center(child: CircularProgressIndicator()) : ListView.builder(
              itemCount: messages.length,
              itemBuilder: (_, i) => MessageBubble(message: messages[i], isMe: messages[i].senderId == me.id),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(children: [
              Expanded(child: TextField(controller: _textC, decoration: const InputDecoration(hintText: 'Type ciphertext...'))),
              const SizedBox(width:8),
              ElevatedButton(onPressed: _send, child: const Text('Send'))
            ]),
          )
        ],
      ),
    );
  }
}
