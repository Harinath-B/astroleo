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
        """
        Initialize the EncryptionManager with ECDH for key exchange and ChaCha20 for encryption.
        """
        
        self.private_key = ec.generate_private_key(
            ec.SECP256R1(),  
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

    def get_public_key(self):
        """Return the public ECDH key as a Base64-encoded string for sharing."""
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return base64.b64encode(public_key_pem).decode('utf-8')

    def generate_shared_secret(self, recipient_public_key_bytes):
        """
        Generate the shared secret using this node's private key and the recipient's public key.
        :param recipient_public_key_bytes: The recipient's public ECDH key in bytes.
        :return: The shared secret (a byte string).
        """
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
        """
        Encrypt data using ChaCha20.
        :param plaintext: Data to encrypt as bytes or string.
        :param symmetric_key: 32-byte ChaCha20 key.
        :return: Encrypted data with nonce prepended.
        """
        
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
        """
        Decrypt data using ChaCha20.
        :param encrypted_data: Data to decrypt, with nonce prepended.
        :param symmetric_key: 32-byte ChaCha20 key.
        :return: Decrypted plaintext as bytes.
        """
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
