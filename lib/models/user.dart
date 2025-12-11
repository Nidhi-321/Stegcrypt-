// lib/models/user.dart
import 'dart:convert';

class User {
  final int id;
  final String username;
  final String? publicKey;

  User({required this.id, required this.username, this.publicKey});

  factory User.fromMap(Map<String, dynamic> m) =>
      User(id: m['id'], username: m['username'], publicKey: m['public_key']);

  factory User.fromJson(String jsonStr) => User.fromMap(jsonDecode(jsonStr));

  Map<String,dynamic> toMap() => {'id': id, 'username': username, 'public_key': publicKey};

  String toJson() => jsonEncode(toMap());
}
