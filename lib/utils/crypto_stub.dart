// lib/utils/crypto_stub.dart
// IMPORTANT: implement real cryptography (RSA/ECDH/Curve25519) here.
// You can use `pointycastle` package or native platform libs.
// For production: generate key pair on device, store private key in secure storage,
// upload public key to server via /register or /user/<id>/public-key endpoint.

class Crypto {
  static Future<String> generateKeyPair() async {
    // return publicKeyPem (and store private key securely)
    throw UnimplementedError('Implement generateKeyPair using pointycastle or native libs');
  }

  static Future<String> encryptWithPublicKey(String publicKeyPem, String plaintext) async {
    // return base64 ciphertext
    throw UnimplementedError('Implement client-side encryption');
  }

  static Future<String> decryptWithPrivateKey(String ciphertextBase64) async {
    throw UnimplementedError('Implement client-side decryption');
  }
}
