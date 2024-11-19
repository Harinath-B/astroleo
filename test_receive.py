from utils.encryption_utils import EncryptionManager
from network.packet import Packet
import requests

def test_receive_endpoint():
    SHARED_KEY = b"sixteenbytekey!!"  # Valid 16-byte AES key
    encryption_manager = EncryptionManager(key=SHARED_KEY)

    # Create a packet
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

    # Serialize the packet
    serialized_data = packet.to_bytes()
    print(f"[DEBUG] Serialized Packet: {serialized_data}")
    print(f"From bytes {Packet.from_bytes(serialized_data, encryption_manager).get_payload()}")

    # Send the packet to the /receive endpoint of Node 3
    destination_node = 3
    response = requests.post(
        f"http://127.0.0.1:{5000 + destination_node}/receive",
        data=serialized_data,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"[DEBUG] Sent Data: {serialized_data.hex()}")  # Debug log
    print(f"[DEBUG] POST Response: {response}")


test_receive_endpoint()