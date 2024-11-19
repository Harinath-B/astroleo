# Import necessary modules
from utils.encryption_utils import EncryptionManager
from satellite_node import SatelliteNode
def test_key_exchange_and_encryption():
    """
    Test ECDH key exchange between two SatelliteNode instances, followed by data encryption and decryption
    using ChaCha20-Poly1305 encryption.
    """
    # Create two EncryptionManager instances (simulating two satellites)
    node_1 = EncryptionManager()
    node_2 = EncryptionManager()

    # Step 1: Node 1 sends its public key to Node 2
    public_key_1 = node_1.get_public_key()

    # Step 2: Node 2 generates the shared secret using Node 1's public key
    symmetric_key_2 = node_2.generate_shared_secret(public_key_1)

    # Step 3: Node 1 generates the shared secret using Node 2's public key
    symmetric_key_1 = node_1.generate_shared_secret(node_2.get_public_key())

    # Step 4: Encrypt data using the shared symmetric key
    message = "Hello, this is a test message!"
    print(f"Original message: {message}")

    encrypted_data = node_1.encrypt_data(message)

    # Step 5: Node 2 decrypts the data using the shared symmetric key
    decrypted_message = node_2.decrypt_data(encrypted_data)

    # Step 6: Assert that the decrypted message matches the original message
    assert decrypted_message == message, f"Decrypted message does not match the original! Expected: {message}, Got: {decrypted_message}"

    print("Test passed! Encryption and decryption successful.")

if __name__ == "__main__":
    test_key_exchange_and_encryption()
