# utils/encyption_utils.py

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os
import base64

class EncryptionManager:
    def __init__(self):
        
        self.private_key = ec.generate_private_key(
            ec.SECP256R1(),  
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )        
        return base64.b64encode(public_key_pem).decode('utf-8')

    def generate_shared_secret(self, recipient_public_key_bytes):
        
        recipient_public_key = serialization.load_pem_public_key(
            recipient_public_key_bytes, backend=default_backend()
        )        
        shared_secret = self.private_key.exchange(ec.ECDH(), recipient_public_key)
        symmetric_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  
            salt=None,
            info=None,
            backend=default_backend()
        ).derive(shared_secret)

        return symmetric_key

    def encrypt(self, plaintext, symmetric_key):
        
        nonce = os.urandom(16)        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        cipher = Cipher(
            algorithms.ChaCha20(symmetric_key, nonce),
            mode=None,
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()        
        return nonce + ciphertext

    def decrypt(self, encrypted_data, symmetric_key):
        
        try:            
            nonce = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            cipher = Cipher(
                algorithms.ChaCha20(symmetric_key, nonce),
                mode=None,
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext

        except Exception as e:
            raise ValueError(f"Decryption failed: {e}, payload: {encrypted_data}")
