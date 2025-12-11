// lib/models/user.dart
class User {
  final dynamic id;
  final String username;
  final String? email;

  User({required this.id, required this.username, this.email});

  factory User.fromMap(Map<String, dynamic> m) {
    return User(
      id: m['id'] ?? m['user_id'] ?? m['uid'],
      username: (m['username'] ?? m['name'] ?? m['email'] ?? '').toString(),
      email: m['email']?.toString(),
    );
  }

  Map<String, dynamic> toMap() => {'id': id, 'username': username, 'email': email};
}
