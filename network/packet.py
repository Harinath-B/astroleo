import struct
from utils.encryption_utils import EncryptionManager

class Packet:
    HEADER_FORMAT = "!BBHHII"  # Added TTL as the last integer
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, version, message_type, source_id, dest_id, sequence_number, payload, ttl=10, encryption_manager=None):
        """
        Initialize a Packet object.

        Args:
            version (int): Protocol version.
            message_type (int): Type of message (1 for data, 2 for RREQ, 3 for RREP).
            source_id (int): ID of the source node.
            dest_id (int): ID of the destination node.
            sequence_number (int): Sequence number for tracking packets.
            payload (str or bytes): Message or data payload.
            ttl (int): Time-to-Live to limit the number of hops.
            encryption_manager (EncryptionManager): Encryption manager for encrypting/decrypting payload.
        """
        self.version = version
        self.message_type = message_type
        self.source_id = source_id
        self.dest_id = dest_id
        self.sequence_number = sequence_number
        self.ttl = ttl  # Time-to-Live for limiting hops
        self.encryption_manager = encryption_manager

        # Ensure the payload is bytes for consistency
        if isinstance(payload, str):
            self.payload = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            self.payload = payload
        else:
            raise TypeError(f"Payload must be of type str or bytes, got {payload, type(payload)}.")


    def to_bytes(self):
        """
        Convert the Packet instance to bytes for transmission.
        """
        encrypted_payload = (
            self.encryption_manager.encrypt(self.payload) if self.encryption_manager else self.payload
        )
        header = struct.pack(
            self.HEADER_FORMAT,
            self.version,
            self.message_type,
            self.source_id,
            self.dest_id,
            self.sequence_number,
            self.ttl
        )
        return header + encrypted_payload

    @staticmethod
    def from_bytes(data, encryption_manager=None):
        """
        Recreate a Packet instance from bytes.

        Args:
            data (bytes): Serialized packet data.
            encryption_manager (EncryptionManager): Encryption manager for decrypting payload.
        """
        if len(data) < Packet.HEADER_SIZE:
            raise ValueError(f"Insufficient data for header: expected {Packet.HEADER_SIZE} bytes, got {len(data)} -> {data} bytes")

        header = data[:Packet.HEADER_SIZE]
        encrypted_payload = data[Packet.HEADER_SIZE:]
        payload = (
            encryption_manager.decrypt(encrypted_payload) if encryption_manager else encrypted_payload
        )

        # Validate that the payload is bytes
        if not isinstance(payload, bytes):
            raise TypeError(f"Decrypted payload must be bytes, got {payload, type(payload)}.")
        
        headers = [*struct.unpack(Packet.HEADER_FORMAT, header)]
        print(f'[DEBUG] {(*headers[:-1], payload, headers[-1], encryption_manager)}')

        return Packet(*headers[:-1], payload, headers[-1], encryption_manager=encryption_manager)



    def get_payload(self):
        """Retrieve the decrypted payload if encryption manager is available, otherwise return the raw payload."""
        # if self.encryption_manager:
        #     return self.encryption_manager.decrypt(self.payload).decode("utf-8")
        return self.payload.decode("utf-8")

    def decrement_ttl(self):
        """Decrease TTL by 1 to manage the hop limit."""
        self.ttl = max(self.ttl - 1, 0)

    def is_valid(self):
        """Check if the packet's TTL is still valid (TTL > 0)."""
        return self.ttl > 0
