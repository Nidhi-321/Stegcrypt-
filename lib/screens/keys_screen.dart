// lib/screens/keys_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';

class KeysScreen extends StatefulWidget {
  const KeysScreen({Key? key}) : super(key: key);

  @override
  State<KeysScreen> createState() => _KeysScreenState();
}

class _KeysScreenState extends State<KeysScreen> {
  bool _loading = false;
  String? _publicKey;
  String? _privateKey;
  String? _message;

  Future<void> _generate() async {
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final res = await ApiService.generateKeyPair();
      // Expecting { "public_key": "...", "private_key": "..." }
      setState(() {
        _publicKey = res['public_key']?.toString() ?? res['publicKey']?.toString();
        _privateKey = res['private_key']?.toString() ?? res['privateKey']?.toString();
      });
    } catch (e) {
      setState(() {
        _message = e.toString();
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _copyToClipboard(String text, {String label = 'Copied'}) async {
    await Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(label)));
  }

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.of(context).size.width > 700;
    return Scaffold(
      appBar: AppBar(title: const Text('Key Manager')),
      body: Padding(
        padding: EdgeInsets.symmetric(horizontal: isWide ? 64 : 16, vertical: 20),
        child: Column(
          children: [
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(14.0),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        _publicKey != null ? 'Public Key ready' : 'Generate a new RSA key pair',
                        style: Theme.of(context).textTheme.subtitle1,
                      ),
                    ),
                    ElevatedButton.icon(
                      onPressed: _loading ? null : _generate,
                      icon: _loading ? const SizedBox(height: 16, width: 16, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.vpn_key),
                      label: const Text('Generate'),
                      style: ElevatedButton.styleFrom(shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                    )
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),
            if (_message != null)
              Text(_message!, style: const TextStyle(color: Colors.red)),
            if (_publicKey != null) ...[
              _keyCard('Public Key', _publicKey!, Colors.green, copyLabel: 'Public key copied'),
              const SizedBox(height: 8),
            ],
            if (_privateKey != null) ...[
              _keyCard('Private Key', _privateKey!, Colors.orange, copyLabel: 'Private key copied', masked: true),
              const SizedBox(height: 8),
            ],
            const SizedBox(height: 12),
            Expanded(child: _buildActions())
          ],
        ),
      ),
    );
  }

  Widget _keyCard(String title, String key, Color accent, {bool masked = false, String copyLabel = 'Copied'}) {
    final display = masked ? _maskKey(key) : key;
    return Card(
      elevation: 3,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
              const Spacer(),
              IconButton(
                tooltip: 'Copy',
                onPressed: () => _copyToClipboard(key, label: copyLabel),
                icon: const Icon(Icons.copy),
              )
            ],
          ),
          const SizedBox(height: 6),
          SelectableText(display, style: const TextStyle(fontFamily: 'monospace', fontSize: 12))
        ]),
      ),
    );
  }

  String _maskKey(String k) {
    if (k.length <= 40) return k;
    return k.substring(0, 24) + '…' + k.substring(k.length - 16);
  }

  Widget _buildActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Next steps:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        const Text('• Share the public key with your recipient.'),
        const Text('• Keep the private key secure and never commit it to git.'),
        const SizedBox(height: 12),
        ElevatedButton.icon(
          onPressed: _publicKey == null ? null : () async {
            // Example: save keys locally (secure storage recommended)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Saved locally (demo)')));
          },
          icon: const Icon(Icons.save),
          label: const Text('Save keys (demo)'),
        ),
      ],
    );
  }
}
