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
    setState(() {
      loading = true;
      error = null;
    });

    final auth = Provider.of<AuthService>(context, listen: false);
    final api = auth.api;
    try {
      final Map<String, dynamic> r = await api.get('/users'); // decoded JSON map
      // backend may return several shapes: {'users': [...]}, {'data': [...]}, or top-level list (rare)
      dynamic rawList;
      if (r.containsKey('users')) {
        rawList = r['users'];
      } else if (r.containsKey('data')) {
        rawList = r['data'];
      } else {
        // maybe the API returned the list directly under a 'data' key or returned an encoded list in 'data'
        rawList = r.values.isNotEmpty && r.values.first is List ? r.values.first : null;
      }

      if (rawList is List) {
        final dynAuth = auth as dynamic;
        final currentId = dynAuth.user != null ? dynAuth.user.id : null;
        final parsed = rawList.map((e) {
          if (e is Map<String, dynamic>) return User.fromMap(e);
          if (e is String) {
            try {
              final m = jsonDecode(e);
              return User.fromMap(m as Map<String, dynamic>);
            } catch (_) {
              return null;
            }
          }
          return null;
        }).whereType<User>().toList();

        // filter out current user if available
        setState(() => users = currentId == null ? parsed : parsed.where((u) => u.id != currentId).toList());
      } else {
        setState(() => error = 'Unexpected users response');
      }
    } catch (e) {
      setState(() => error = 'Error loading users: $e');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthService>(context, listen: false);

    return Scaffold(
      appBar: AppBar(title: const Text('Contacts'), actions: [
        IconButton(onPressed: () => auth.logout(), icon: const Icon(Icons.logout))
      ]),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(child: Text(error!))
              : ListView.builder(
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
