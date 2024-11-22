# network/packet.py

import struct

class Packet:
    HEADER_FORMAT = "!BBHHII"  
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, version, message_type, source_id, dest_id, sequence_number, payload, ttl=10):
       
        self.version = version
        self.message_type = message_type
        self.source_id = source_id
        self.dest_id = dest_id
        self.sequence_number = sequence_number
        self.ttl = ttl  
        self.payload = payload

    def to_bytes(self):

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

        if len(data) < Packet.HEADER_SIZE:
            raise ValueError(f"Insufficient data for header: expected {Packet.HEADER_SIZE} bytes, got {len(data)} bytes")

        header = data[:Packet.HEADER_SIZE]
        payload = data[Packet.HEADER_SIZE:]
        version, message_type, source_id, dest_id, sequence_number, ttl = struct.unpack(Packet.HEADER_FORMAT, header)
        return Packet(version, message_type, source_id, dest_id, sequence_number, payload, ttl)

    def get_payload(self):

        return self.payload.decode()

    def set_encrypted_payload(self, encrypted_payload):

        self.payload = encrypted_payload

    def is_valid(self):

        return self.ttl > 0

    def decrement_ttl(self):

        self.ttl = max(self.ttl - 1, 0)
