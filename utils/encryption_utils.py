from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import base64
import os

class EncryptionManager:
    def __init__(self):
        """
        Initialize the EncryptionManager with ECDH for key exchange and ChaCha20-Poly1305 for encryption.
        """
        # Generate ECDH public/private key pair for key exchange (P-256 curve)
        self.private_key = ec.generate_private_key(
            ec.SECP256R1(),  # SECP256R1 (P-256) curve for ECDH
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.shared_symmetric_key = None  # Will be set after key exchange


    def get_public_key(self):
        """Return the public ECDH key as a Base64-encoded string for sharing."""
        public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        # Encode the PEM bytes in Base64 for HTTP transmission
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
        # Perform ECDH key exchange and get the shared secret
        shared_secret = self.private_key.exchange(ec.ECDH(), recipient_public_key)

        # Use HKDF to derive a symmetric key from the shared secret
        self.shared_symmetric_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes for a ChaCha20-Poly1305 key (256-bit key)
            salt=None,
            info=None,
            backend=default_backend()
        ).derive(shared_secret)

        return self.shared_symmetric_key

    def encrypt(self, plaintext):
        """Encrypt data using the shared symmetric key with ChaCha20-Poly1305."""
        if self.shared_symmetric_key:
            cipher = ChaCha20Poly1305(self.shared_symmetric_key)
            nonce = os.urandom(12)  # Generate a random 12-byte nonce
            ciphertext = cipher.encrypt(nonce, plaintext, None)  # Encrypt the plaintext
            return nonce + ciphertext  # Prepend nonce to ciphertext
        else:
            raise ValueError("No symmetric key found for encryption")

    def decrypt(self, encrypted_data):
        """Decrypt data using the shared symmetric key with ChaCha20-Poly1305."""
        if self.shared_symmetric_key:
            nonce = encrypted_data[:12]  # The first 12 bytes are the nonce
            ciphertext = encrypted_data[12:]  # The rest is the ciphertext
            cipher = ChaCha20Poly1305(self.shared_symmetric_key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)  # Decrypt the ciphertext
            return plaintext.decode('utf-8')
        else:
            raise ValueError("No symmetric key found for decryption")
