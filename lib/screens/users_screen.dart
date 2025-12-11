// lib/screens/users_screen.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/user.dart';
import 'chat_screen.dart';

class UsersScreen extends StatefulWidget {
  const UsersScreen({super.key});
  @override
  State<UsersScreen> createState() => _UsersScreenState();
}

class _UsersScreenState extends State<UsersScreen> {
  List<User> users = [];
  bool loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  Future<void> _loadUsers() async {
    setState((){ loading = true; });
    final auth = Provider.of<AuthService>(context, listen: false);
    final api = auth.api;
    try {
      final r = await api.get('/users');
      if (r.statusCode == 200) {
        final List<dynamic> list = jsonDecode(r.body);
        setState(() => users = list.map((e) => User.fromMap(e)).where((u) => u.id != auth.user!.id).toList());
      } else {
        setState(() => error = 'Failed to load users');
      }
    } catch (e) {
      setState(() => error = 'Error: $e');
    } finally {
      setState((){ loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context, listen: false);

    return Scaffold(
      appBar: AppBar(title: const Text('Contacts'), actions: [
        IconButton(onPressed: () => auth.logout(), icon: const Icon(Icons.logout))
      ]),
      body: loading ? const Center(child:CircularProgressIndicator()) : error != null ? Center(child: Text(error!)) : ListView.builder(
        itemCount: users.length,
        itemBuilder: (_, i) {
          final u = users[i];
          return ListTile(
            title: Text(u.username),
            subtitle: Text('ID: ${u.id}'),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ChatScreen(otherUser: u))),
          );
        },
      ),
    );
  }
}
