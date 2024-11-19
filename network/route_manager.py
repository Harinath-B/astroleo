import requests
from network.packet import Packet
from utils.logging_utils import log
import random

class RouteManager:
    def __init__(self, node):
        self.node = node

    def forward_packet(self, packet):
        """
        Forward the packet to the next hop or a random neighbor.

        Args:
            packet (Packet): The packet to forward.
        """
        network = self.node.network
        dest_id = packet.dest_id
        if dest_id in network.routing_table:
            next_hop = network.routing_table[dest_id][0]
            self.send_to_node(next_hop, packet)
            return True
        elif network.neighbors:
            random_neighbor = random.choice(list(network.neighbors.keys()))
            self.send_to_node(random_neighbor, packet)
            log(self.node.general_logger, f"Node {self.node.node_id}: Forwarded packet to random neighbor {random_neighbor} for destination {dest_id}")
            return True
        else:
            log(self.node.general_logger, f"Node {self.node.node_id}: No neighbors to forward packet to for destination {dest_id}")
            return False

    def send_to_node(self, neighbor_id, packet):
        """
        Send the packet to a specific neighbor.

        Args:
            neighbor_id (int): ID of the neighbor node.
            packet (Packet): The packet to send.
        """
        try:
            requests.post(
                f"http://127.0.0.1:{5000 + int(neighbor_id)}/receive",
                data=packet.to_bytes()
            )
        except requests.RequestException:
            log(self.node.general_logger, f"Failed to send packet to Node {neighbor_id}", level="error")
