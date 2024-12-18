import base64

from utils.encryption_utils import EncryptionManager

def test_encryption_manager_with_5_nodes():
    nodes = [EncryptionManager() for _ in range(5)]
    public_keys = [base64.b64decode(node.get_public_key().encode('utf-8')) for node in nodes]    
    symmetric_keys = {}

    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i != j:                
                symmetric_keys[(i, j)] = nodes[i].generate_shared_secret(public_keys[j])

    for i in range(len(nodes)):
        for j in range(len(nodes)):
            if i != j:                
                symmetric_key = symmetric_keys[(i, j)]                
                plaintext = f"Message from Node {i} to Node {j}."
                print(f"Encrypting: {plaintext}")
                encrypted_data = nodes[i].encrypt(plaintext, symmetric_key)
                print(f"Encrypted data: {encrypted_data}")
                decrypted_message = nodes[j].decrypt(encrypted_data, symmetric_key)
                print(f"Decrypted: {decrypted_message.decode('utf-8')}")                
                assert decrypted_message.decode('utf-8') == plaintext, "Decryption failed!"

    print("Test passed: All nodes successfully exchanged and decrypted messages.")

test_encryption_manager_with_5_nodes()
