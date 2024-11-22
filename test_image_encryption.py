import base64
import zlib
import os
import requests
from PIL import Image

from utils.encryption_utils import EncryptionManager

session = requests.Session()
session.trust_env = False

def test_image_encryption_decryption_with_compression():    
    
    node1 = EncryptionManager()
    node2 = EncryptionManager()
    node1_public_key = base64.b64decode(node1.get_public_key())
    node2_public_key = base64.b64decode(node2.get_public_key())
    symmetric_key_node1 = node1.generate_shared_secret(node2_public_key)
    symmetric_key_node2 = node2.generate_shared_secret(node1_public_key)    
    assert symmetric_key_node1 == symmetric_key_node2, "Symmetric keys do not match!"
    symmetric_key = symmetric_key_node1      

    test_image_path = "test_image.png"       
    encrypted_image_path = "test_image.enc"  
    decrypted_image_path = "decrypted_image.png"  
    
    if not os.path.exists(test_image_path):
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))  
        img.save(test_image_path)
    
    with open(test_image_path, "rb") as img_file:
        original_image_data = img_file.read()    
    compressed_image_data = zlib.compress(original_image_data)
    print(f"Original image size: {len(original_image_data)} bytes")
    print(f"Compressed image size: {len(compressed_image_data)} bytes")
    
    encrypted_image_data = node1.encrypt(compressed_image_data, symmetric_key)
    with open(encrypted_image_path, "wb") as enc_file:
        enc_file.write(encrypted_image_data)
    print(f"Image compressed and encrypted successfully. Encrypted file: {encrypted_image_path}")
    
    with open(encrypted_image_path, "rb") as enc_file:
        encrypted_image_data = enc_file.read()
    
    decrypted_compressed_image_data = node2.decrypt(encrypted_image_data, symmetric_key)    
    decompressed_image_data = zlib.decompress(decrypted_compressed_image_data)    
    with open(decrypted_image_path, "wb") as dec_file:
        dec_file.write(decompressed_image_data)
    print(f"Image decrypted and decompressed successfully. Decrypted file: {decrypted_image_path}")    
    assert original_image_data == decompressed_image_data, "Decompressed image does not match the original!"
    print("Test passed: The decrypted and decompressed image matches the original.")

if __name__ == "__main__":
    test_image_encryption_decryption_with_compression()
