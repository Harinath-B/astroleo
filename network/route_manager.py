# network/route_manager.py

import requests
from utils.logging_utils import log
from network.packet import Packet
import zlib

session = requests.Session()
session.trust_env = False

class RouteManager:

    def __init__(self, node):

        self.node = node
        self.image_chunks = {}  

    def forward_packet(self, packet):

        if not self.node.is_active():
            log(self.node.general_logger, "Node is offline and cannot forward packets.")
            return False

        network = self.node.network
        dest_id = packet.dest_id
        if dest_id == self.node.node_id:
            log(self.node.general_logger, f"Node {self.node.node_id}: Received packet for destination {dest_id}")
            return True

        if dest_id in network.routing_table:
            next_hop = network.routing_table[dest_id][0]
            if next_hop not in self.node.shared_symmetric_keys:
                log(self.node.general_logger, f"Node {self.node.node_id}: No symmetric key with Node {next_hop}. Initiating key exchange.")
                if not self.node.exchange_keys_with_neighbor(next_hop):
                    log(self.node.general_logger, f"Node {self.node.node_id}: Key exchange with Node {next_hop} failed. Cannot forward packet.", level="error")
                    return False

            log(self.node.general_logger, f"Node {self.node.node_id}: Forwarding packet to next hop {next_hop} for destination {dest_id}")
            self.send_to_node(next_hop, packet)
            return True
        log(self.node.general_logger, f"Node {self.node.node_id}: No route found for destination {dest_id}. Initiating fallback.")
        return self.flood_packet(packet)

    def flood_packet(self, packet):

        if not self.node.is_active():
            log(self.node.general_logger, "Node is offline and cannot flood packets.")
            return False

        for neighbor_id in self.node.network.neighbors:
            log(self.node.general_logger, f"Node {self.node.node_id}: Flooding packet to Node {neighbor_id}")
            self.send_to_node(neighbor_id, packet)
        return True

    def send_to_node(self, neighbor_id, packet):

        if not self.node.is_active():
            log(self.node.general_logger, "Node is offline and cannot send packets.")
            return

        if neighbor_id not in self.node.shared_symmetric_keys:
            log(self.node.general_logger, f"Node {self.node.node_id}: No symmetric key with Node {neighbor_id}. Cannot send packet.", level="error")
            return
        shared_key = self.node.shared_symmetric_keys[neighbor_id]
        log(self.node.general_logger, f"{self.node.node_id} Shared key with {neighbor_id} - {shared_key}")
        encrypted_payload = self.node.encryption_manager.encrypt(packet.payload, shared_key)
        packet.payload = encrypted_payload
        serialized_packet = packet.to_bytes()
        log(self.node.general_logger, f"Serialized packet sent: {serialized_packet}")
        log(self.node.general_logger, f"Shared symmetric key for Node {neighbor_id}: {shared_key}")

        if packet.message_type == 2:
            url = f"http://10.35.70.23:{5000 + int(neighbor_id)}/receive_image_from_satellite"
        else:
            url = f"http://10.35.70.23:{5000 + int(neighbor_id)}/receive"
        try:
            response = session.post(url, data=serialized_packet)
            if response.status_code == 200:
                log(self.node.general_logger, f"Node {self.node.node_id}: Successfully sent packet to Node {neighbor_id}")
            else:
                log(self.node.general_logger, f"Failed to send packet to Node {neighbor_id}: {response.status_code}", level="error")

        except requests.RequestException as e:
            log(self.node.general_logger, f"Failed to send packet to Node {neighbor_id}: {str(e)}", level="error")

    def receive_packet(self, serialized_packet):

        if not self.node.is_active():
            log(self.node.general_logger, "Node is offline and cannot receive packets.")
            return

        try:
            packet = Packet.from_bytes(serialized_packet)

        except Exception as e:
            log(self.node.general_logger, f"Error deserializing packet: {e}", level="error")
            return
            
        sender_id = packet.source_id
        if sender_id not in self.node.shared_symmetric_keys:
            log(self.node.general_logger, f"No symmetric key with Node {sender_id}. Cannot decrypt packet.", level="error")
            return

        try:
            decrypted_payload = self.node.encryption_manager.decrypt(packet.payload, self.node.shared_symmetric_keys[sender_id])

        except Exception as e:
            log(self.node.general_logger, f"Failed to decrypt packet payload: {e}", level="error")
            return

        if packet.message_type == 2:  
            try:
                metadata, chunk = decrypted_payload.split(b"|", 1)
                chunk_number, total_chunks = map(int, metadata.decode('utf-8').split("/"))                
                if sender_id not in self.image_chunks:
                    self.image_chunks[sender_id] = {}
                self.image_chunks[sender_id][chunk_number] = chunk                
                if len(self.image_chunks[sender_id]) == total_chunks:
                    full_image_data = b"".join(self.image_chunks[sender_id][i] for i in range(1, total_chunks + 1))
                    try:
                        decompressed_image_data = zlib.decompress(full_image_data)
                        image_path = self.node.save_received_image(decompressed_image_data, sender_id)
                        log(self.node.general_logger, f"Image received and saved at {image_path}")

                    except Exception as e:
                        log(self.node.general_logger, f"Failed to decompress and save image: {e}", level="error")
                    finally:
                        del self.image_chunks[sender_id]

            except Exception as e:
                log(self.node.general_logger, f"Error processing image chunk: {e}", level="error")
        else:
            log(self.node.general_logger, f"Packet received: {decrypted_payload.decode('utf-8')}")
