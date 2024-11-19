from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import os
import base64


class EncryptionManager:
    def __init__(self, key=None):
        """
        Initialize the EncryptionManager with AES-GCM encryption and decryption.
        :param key: A string or bytes key for AES encryption. If not provided, a random 16-byte key is generated.
        """
        if key is None:
            self.key = os.urandom(32)  # 32 bytes for AES-256
        else:
            # Derive a strong key using PBKDF2HMAC for consistent length
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # Key length for AES-GCM
                salt=b"fixed_salt",  # Fixed salt ensures consistent key derivation
                iterations=100000,
                backend=default_backend()
            )
            self.key = kdf.derive(key.encode('utf-8') if isinstance(key, str) else key)

    def encrypt(self, plaintext):
        """
        Encrypt a plaintext message using AES-GCM.
        :param plaintext: The plaintext message to encrypt (bytes).
        :return: Encrypted message (bytes) with nonce prepended.
        """
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12)  # Generate a random 12-byte nonce
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        encrypted_data = nonce + ciphertext  # Prepend the nonce to the ciphertext
        print(f"[DEBUG] Encrypt: Nonce={nonce.hex()}, Ciphertext={ciphertext.hex()}")
        return encrypted_data  # Return the raw bytes

    def decrypt(self, encrypted_data):
        """
        Decrypt an encrypted message using AES-GCM.
        :param encrypted_data: The encrypted message (bytes) with nonce prepended.
        :return: The decrypted plaintext message (string).
        """
        nonce = encrypted_data[:12]  # Extract the first 12 bytes as the nonce
        ciphertext = encrypted_data[12:]  # The rest is the ciphertext
        aesgcm = AESGCM(self.key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        print(f"[DEBUG] Decrypt: Nonce={nonce.hex()}, Plaintext={plaintext.decode('utf-8')}")
        return plaintext.decode('utf-8')  # Decode plaintext to a string
