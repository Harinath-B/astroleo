import requests

from app.satellite_node import SatelliteNode

session = requests.Session()
session.trust_env = False

def test_key_exchange_and_encrypted_communication():
    
    node_1 = SatelliteNode(node_id=1, position=(0, 0, 0))
    node_2 = SatelliteNode(node_id=2, position=(10, 0, 0))    
    public_key_1 = node_1.encryption_manager.get_public_key()
    response_1 = session.post(
        f"http://10.35.70.23:{5001}/exchange_key", 
        json={"node_id": 2, "public_key": public_key_1}
    )
    assert response_1.status_code == 200, f"Key exchange with Node 2 failed!{response_1.status_code}"    
    public_key_2 = node_2.encryption_manager.get_public_key()
    response_2 = session.post(
        f"http://10.35.70.23:{5002}/exchange_key", 
        json={"node_id": 1, "public_key": public_key_2}
    )
    assert response_2.status_code == 200, "Key exchange with Node 1 failed!"
    print(node_1.shared_symmetric_keys, node_2.shared_symmetric_keys)
    
    assert 2 in node_1.shared_symmetric_keys, "Node 1 failed to establish symmetric key with Node 2!"
    assert 1 in node_2.shared_symmetric_keys, "Node 2 failed to establish symmetric key with Node 1!"
    print("Key exchange successful between Node 1 and Node 2!")    

    message = "Hello, Node 2! This is Node 1."
    encrypted_message = node_1.encryption_manager.encrypt_data(message, node_1.shared_symmetric_keys[2])    
    decrypted_message = node_2.encryption_manager.decrypt_data(encrypted_message, node_2.shared_symmetric_keys[1])
    assert message == decrypted_message, "Decrypted message does not match the original!"
    print("Encrypted communication test passed!")

if __name__ == "__main__":
    test_key_exchange_and_encrypted_communication()
