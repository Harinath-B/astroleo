# network/packet.py

import struct

class Packet:
    HEADER_FORMAT = "!BBHHII"  # Version, MessageType, SourceID, DestID, SequenceNumber, TTL
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, version, message_type, source_id, dest_id, sequence_number, payload, ttl=10):
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
        """
        self.version = version
        self.message_type = message_type
        self.source_id = source_id
        self.dest_id = dest_id
        self.sequence_number = sequence_number
        self.ttl = ttl  # Time-to-Live for limiting hops
        self.payload = payload

        # # Ensure the payload is bytes for consistency
        # if isinstance(payload, str):
        #     self.payload = payload.encode("utf-8")
        # elif isinstance(payload, bytes):
        #     self.payload = payload
        # else:
        #     raise TypeError(f"Payload must be of type str or bytes, got {type(payload)}.")

    def to_bytes(self):
        """
        Convert the Packet instance to bytes for transmission.

        Returns:
            bytes: Serialized packet.
        """
        header = struct.pack(
            self.HEADER_FORMAT,
            self.version,
            self.message_type,
            self.source_id,
            self.dest_id,
            self.sequence_number,
            self.ttl
        )
        serialized_packet = header + self.payload
        return serialized_packet

    @staticmethod
    def from_bytes(data):
        """
        Recreate a Packet instance from bytes.

        Args:
            data (bytes): Serialized packet.

        Returns:
            Packet: Deserialized Packet instance.
        """
        if len(data) < Packet.HEADER_SIZE:
            raise ValueError(f"Insufficient data for header: expected {Packet.HEADER_SIZE} bytes, got {len(data)} bytes")

        header = data[:Packet.HEADER_SIZE]
        payload = data[Packet.HEADER_SIZE:]

        version, message_type, source_id, dest_id, sequence_number, ttl = struct.unpack(Packet.HEADER_FORMAT, header)
        return Packet(version, message_type, source_id, dest_id, sequence_number, payload, ttl)

    def get_payload(self):
        """
        Retrieve the payload as a string.

        Returns:
            str: Decoded payload.
        """
        return self.payload.decode()

    def set_encrypted_payload(self, encrypted_payload):
        """
        Set an encrypted payload.

        Args:
            encrypted_payload (bytes): Encrypted payload.
        """
        self.payload = encrypted_payload

    def is_valid(self):
        """
        Check if the packet's TTL is still valid (TTL > 0).

        Returns:
            bool: True if TTL > 0, False otherwise.
        """
        return self.ttl > 0

    def decrement_ttl(self):
        """
        Decrease TTL by 1 to manage the hop limit.
        """
        self.ttl = max(self.ttl - 1, 0)
