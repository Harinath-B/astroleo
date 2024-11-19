from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import os

class EncryptionManager:
    def __init__(self, key=None):
        # if len(key) not in (16, 24, 32):
        #     raise ValueError(f"Invalid key size: {len(key)} bytes. Key must be 16, 24, or 32 bytes long.")
        self.key = key if key else os.urandom(16)


    def encrypt(self, data):
        """
        Encrypts data using AES-CBC mode with PKCS7 padding.
        Returns the IV concatenated with the ciphertext.
        """
        iv = os.urandom(16)  # Generate a random IV
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Add PKCS7 padding
        padder = PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        
        # Encrypt and return IV + ciphertext
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv + ciphertext

    def decrypt(self, encrypted_data):
        """
        Decrypts data using AES-CBC mode with PKCS7 unpadding.
        Assumes the IV is prepended to the ciphertext.
        """
        iv = encrypted_data[:16]  # Extract IV (first 16 bytes)
        ciphertext = encrypted_data[16:]  # Extract ciphertext
        
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # Decrypt and remove PKCS7 padding
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = PKCS7(128).unpadder()
        data = unpadder.update(padded_data) + unpadder.finalize()
        
        return data
