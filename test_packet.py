from utils.encryption_utils import EncryptionManager
from network.packet import Packet
def test_packet():
    SHARED_KEY = b"sixteenbytekey!!"  # Valid 16-byte AES key
    encryption_manager = EncryptionManager(key=SHARED_KEY)

    # Create a packet
    original_payload = "This is a test message"
    packet = Packet(
        version=1,
        message_type=1,
        source_id=1,
        dest_id=2,
        sequence_number=123,
        payload=original_payload,
        ttl=10,
        encryption_manager=encryption_manager
    )

    # Serialize the packet
    serialized_data = packet.to_bytes()
    print(f"Serialized Packet: {serialized_data}")

    # Deserialize the packet
    deserialized_packet = Packet.from_bytes(serialized_data, encryption_manager=encryption_manager)
    print(f"Deserialized Packet Payload: {deserialized_packet.get_payload()}")

    # Verify the payload matches
    assert deserialized_packet.get_payload() == original_payload
    print("Test Passed: Payload matches!")

test_packet()
