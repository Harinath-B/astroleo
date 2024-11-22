from network.packet import Packet
import requests

from utils.encryption_utils import EncryptionManager

session = requests.Session()
session.trust_env = False

def test_receive_endpoint():
    SHARED_KEY = b"sixteenbytekey!!"  
    encryption_manager = EncryptionManager(key=SHARED_KEY)
    
    original_payload = "Test message for Node 3"
    packet = Packet(
        version=1,
        message_type=1,
        source_id=1,
        dest_id=3,
        sequence_number=123,
        payload=original_payload,
        ttl=10,
        encryption_manager=encryption_manager
    )    
    serialized_data = packet.to_bytes()
    print(f"[DEBUG] Serialized Packet: {serialized_data}")
    print(f"From bytes {Packet.from_bytes(serialized_data, encryption_manager).get_payload()}")    
    destination_node = 3
    response = session.post(
        f"http://10.35.70.23:{5000 + destination_node}/receive",
        data=serialized_data,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"[DEBUG] Sent Data: {serialized_data.hex()}")  
    print(f"[DEBUG] POST Response: {response}")

if __name__ == "__main__":
    test_receive_endpoint()