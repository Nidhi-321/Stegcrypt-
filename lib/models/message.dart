// lib/models/message.dart
class MessageModel {
  final int id;
  final int senderId;
  final int receiverId;
  final String ciphertext;
  final DateTime createdAt;

  MessageModel({required this.id, required this.senderId, required this.receiverId, required this.ciphertext, required this.createdAt});

  factory MessageModel.fromMap(Map<String, dynamic> m) => MessageModel(
    id: m['id'],
    senderId: m['sender_id'],
    receiverId: m['receiver_id'],
    ciphertext: m['ciphertext'],
    createdAt: DateTime.parse(m['created_at']),
  );
}
