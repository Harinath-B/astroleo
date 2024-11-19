from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import os

class EncryptionManager:
    def __init__(self, key=None, pad=None):
        # if len(key) not in (16, 24, 32):
        #     raise ValueError(f"Invalid key size: {len(key)} bytes. Key must be 16, 24, or 32 bytes long.")
        self.key = key if key else os.urandom(16)
        self.pad = pad if pad else PKCS7(128)


    def encrypt(self, data):
        """
        Encrypt data with padding.
        """
        padder = self.pad.padder()
        padded_data = padder.update(data) + padder.finalize()  # Add padding
        iv = os.urandom(16)  # Generate a random IV
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        print(f"[DEBUG] Encrypt: IV={iv.hex()}, Encrypted Data={encrypted_data.hex()}")  # Debug log
        return iv + encrypted_data  # Prepend IV to the encrypted data


    def decrypt(self, data):
        """
        Decrypt data and remove padding.
        """
        print(f"[DEBUG] decrypt: {data.hex()}", flush=True)
        iv, ciphertext = data[:16], data[16:]  # Extract IV and ciphertext
        print(f"[DEBUG] Decrypt: IV={iv.hex()}, Ciphertext={ciphertext.hex()}", flush=True)  # Debug log
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        print(f"[DEBUG] Decrypted (Padded) Data: {padded_data.hex()}", flush=True)  # Debug log
        unpadder = self.pad.unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
        print(f"[DEBUG] Plaintext: {plaintext.decode('utf-8')}", flush=True)  # Debug log
        return plaintext