import struct

class Packet:
    HEADER_FORMAT = "!BBHHII"  # Added TTL as the last integer
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
            payload (str): Message or data payload.
            ttl (int): Time-to-Live to limit the number of hops.
        """
        self.version = version
        self.message_type = message_type  # 1 for data, 2 for RREQ, 3 for RREP
        self.source_id = source_id
        self.dest_id = dest_id
        self.sequence_number = sequence_number
        self.payload = payload
        self.ttl = ttl  # Time-to-Live for limiting hops

    def to_bytes(self):
        """
        Convert the Packet instance to bytes for transmission.
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
        return header + self.payload.encode('utf-8')

    @staticmethod
    def from_bytes(data):
        """
        Recreate a Packet instance from bytes.
        """
        header = data[:Packet.HEADER_SIZE]
        payload = data[Packet.HEADER_SIZE:].decode('utf-8')
        version, message_type, source_id, dest_id, sequence_number, ttl = struct.unpack(Packet.HEADER_FORMAT, header)
        return Packet(version, message_type, source_id, dest_id, sequence_number, payload, ttl)

    def decrement_ttl(self):
        """Decrease TTL by 1 to manage the hop limit."""
        self.ttl = max(self.ttl - 1, 0)

    def is_valid(self):
        """Check if the packet's TTL is still valid (TTL > 0)."""
        return self.ttl > 0
