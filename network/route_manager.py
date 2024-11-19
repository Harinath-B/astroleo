import requests
from network.packet import Packet
from utils.logging_utils import log
import time

class RouteManager:
    def __init__(self, node):
        self.node = node

    def forward_packet(self, packet):
        """
        Forward the packet to the next hop based on the routing table.
        If no route exists, use a fallback mechanism (e.g., flooding).
        """
        network = self.node
        dest_id = packet.dest_id

        # Check if the destination is this node
        if dest_id == self.node.node_id:
            log(self.node.general_logger, f"Node {self.node.node_id}: Received packet for destination {dest_id}")
            return True  # The packet has reached its destination

        # Check the routing table for the next hop
        if dest_id in network.routing_table:
            next_hop = network.routing_table[dest_id][0]  # Get the next hop from the routing table
            log(self.node.general_logger, f"Node {self.node.node_id}: Forwarding packet to next hop {next_hop} for destination {dest_id}")
            self.send_to_node(next_hop, packet)  # Forward the packet to the next hop
            return True
        else:
            log(self.node.general_logger, f"Node {self.node.node_id}: No route found for destination {dest_id}. Initiating fallback.")
            # Fallback mechanism: Flood the packet to all neighbors
            return self.flood_packet(packet)

    def flood_packet(self, packet):
        """
        Flood the packet to all neighbors.
        """
        for neighbor_id in self.node.neighbors:
            log(self.node.general_logger, f"Node {self.node.node_id}: Flooding packet to Node {neighbor_id}")
            self.send_to_node(neighbor_id, packet)
        return True

    def send_to_node(self, neighbor_id, packet):
        """
        Send the packet to a specific neighbor node.
        """
        url = f"http://127.0.0.1:{5000 + int(neighbor_id)}/receive"
        try:
            response = requests.post(url, data=packet.to_bytes())
            if response.status_code == 200:
                log(self.node.general_logger, f"Node {self.node.node_id}: Successfully sent packet to Node {neighbor_id}")
            else:
                log(self.node.general_logger, f"Failed to send packet to Node {neighbor_id}: {response.status_code}", level="error")
        except requests.RequestException as e:
            log(self.node.general_logger, f"Failed to send packet to Node {neighbor_id}: {str(e)}", level="error")
