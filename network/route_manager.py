import requests
from utils.logging_utils import log
from network.packet import Packet

class RouteManager:
    def __init__(self, node):
        self.node = node

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
        else:
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
        encrypted_payload = self.node.encryption_manager.encrypt(packet.payload, shared_key)

        
        packet.payload = encrypted_payload
        serialized_packet = packet.to_bytes()
        log(self.node.general_logger, f"Serialized packet sent: {serialized_packet}")
        log(self.node.general_logger, f"Shared symmetric key for Node {neighbor_id}: {shared_key}")

        url = f"http://127.0.0.1:{5000 + int(neighbor_id)}/receive"
        try:
            response = requests.post(url, data=serialized_packet)
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

        log(self.node.general_logger, f"Received packet data: {serialized_packet}")

        try:
            packet = Packet.from_bytes(serialized_packet)
        except Exception as e:
            log(self.node.general_logger, f"Error deserializing packet: {e}", level="error")
            return

        sender_id = packet.source_id
        if sender_id not in self.node.shared_symmetric_keys:
            log(self.node.general_logger, f"Node {self.node.node_id}: No symmetric key with Node {sender_id}. Cannot decrypt packet.", level="error")
            return

        log(self.node.general_logger, f"Shared symmetric key for Node {sender_id}: {self.node.shared_symmetric_keys[sender_id]}")

        try:
            decrypted_payload = self.node.encryption_manager.decrypt(packet.payload, self.node.shared_symmetric_keys[sender_id])
            log(self.node.general_logger, f"Node {self.node.node_id}: Successfully decrypted packet from Node {sender_id}; Payload: {decrypted_payload}")
        except Exception as e:
            log(self.node.general_logger, f"Node {self.node.node_id}: Failed to decrypt packet from Node {sender_id} - {e} - payload: {packet.payload}", level="error")
            return

        self.node.last_received_packet = packet
        
        if packet.dest_id == self.node.node_id:
            log(self.node.general_logger, f"Node {self.node.node_id}: Packet delivered successfully. Payload: {packet.payload}")
        else:
            self.forward_packet(packet)
