from utils.encryption_utils import EncryptionManager  
import base64
import zlib
import os

session = requests.Session()
session.trust_env = False

def test_image_encryption_decryption_with_compression():
    """
    Test the encryption, compression, and decryption of an image using EncryptionManager.
    """
    # Initialize encryption managers for two nodes (to simulate key exchange)
    node1 = EncryptionManager()
    node2 = EncryptionManager()

    # Exchange public keys and generate shared symmetric keys
    node1_public_key = base64.b64decode(node1.get_public_key())
    node2_public_key = base64.b64decode(node2.get_public_key())

    symmetric_key_node1 = node1.generate_shared_secret(node2_public_key)
    symmetric_key_node2 = node2.generate_shared_secret(node1_public_key)

    # Assert that both nodes derived the same symmetric key
    assert symmetric_key_node1 == symmetric_key_node2, "Symmetric keys do not match!"

    symmetric_key = symmetric_key_node1  # Use the shared key

    # Define paths for testing
    test_image_path = "test_image.png"       # Input image file
    encrypted_image_path = "test_image.enc"  # Encrypted file
    decrypted_image_path = "decrypted_image.png"  # Decrypted image file

    # Create a sample image for testing (if not exists)
    if not os.path.exists(test_image_path):
        from PIL import Image
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))  # Create a red image
        img.save(test_image_path)

    # Step 1: Compress and Encrypt the image
    with open(test_image_path, "rb") as img_file:
        original_image_data = img_file.read()

    # Compress the image data
    compressed_image_data = zlib.compress(original_image_data)
    print(f"Original image size: {len(original_image_data)} bytes")
    print(f"Compressed image size: {len(compressed_image_data)} bytes")

    # Encrypt the compressed image data
    encrypted_image_data = node1.encrypt(compressed_image_data, symmetric_key)
    with open(encrypted_image_path, "wb") as enc_file:
        enc_file.write(encrypted_image_data)

    print(f"Image compressed and encrypted successfully. Encrypted file: {encrypted_image_path}")

    # Step 2: Decrypt and Decompress the image
    with open(encrypted_image_path, "rb") as enc_file:
        encrypted_image_data = enc_file.read()

    # Decrypt the image data
    decrypted_compressed_image_data = node2.decrypt(encrypted_image_data, symmetric_key)

    # Decompress the decrypted image data
    decompressed_image_data = zlib.decompress(decrypted_compressed_image_data)

    # Save the decompressed image to a file
    with open(decrypted_image_path, "wb") as dec_file:
        dec_file.write(decompressed_image_data)

    print(f"Image decrypted and decompressed successfully. Decrypted file: {decrypted_image_path}")

    # Step 3: Validate the decompressed image
    assert original_image_data == decompressed_image_data, "Decompressed image does not match the original!"
    print("Test passed: The decrypted and decompressed image matches the original.")

# Run the test
if __name__ == "__main__":
    test_image_encryption_decryption_with_compression()

