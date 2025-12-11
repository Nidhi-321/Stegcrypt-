// lib/widgets/message_bubble.dart
import 'package:flutter/material.dart';
import '../models/message.dart';

class MessageBubble extends StatelessWidget {
  final MessageModel message;
  final bool isMe;
  const MessageBubble({required this.message, required this.isMe, super.key});

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: isMe ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal:12, vertical:6),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isMe ? Colors.indigo.shade100 : Colors.grey.shade200,
          borderRadius: BorderRadius.circular(12),
        ),
        width: MediaQuery.of(context).size.width * 0.72,
        child: Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
          Text(message.ciphertext, style: const TextStyle(fontSize: 14)),
          const SizedBox(height: 6),
          Text(message.createdAt.toLocal().toString(), style: const TextStyle(fontSize: 10, color: Colors.black54)),
        ]),
      ),
    );
  }
}
