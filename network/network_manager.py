import requests
import time
import threading
import random
from config import DISCOVERY_RANGE, BROADCAST_INTERVAL, BASE_PORT
from utils.logging_utils import log, setup_logger
from utils.distance_utils import calculate_distance

class NetworkManager:
    def __init__(self, node):
        self.node = node
        self.neighbors = {}
        self.routing_table = {}
        self.logger = setup_logger(self.node.node_id, "general")

    def update_position(self, neighbor_id, position):
        distance = calculate_distance(self.node.position, position)
        if distance <= DISCOVERY_RANGE:
            self.neighbors[neighbor_id] = (position, distance)
            self.routing_table[neighbor_id] = (neighbor_id, distance)
            log(self.logger, f"Node {self.node.node_id}: Added direct neighbor {neighbor_id} with distance {distance}")
            self.propagate_routing_table()

    def update_routing_table(self, received_table, sender_id):
        """Update routing table based on a received routing table from a neighbor."""
        # Check if sender is a known neighbor
        if sender_id not in self.neighbors:
            log(self.logger, f"Node {self.node.node_id}: Received routing table from unknown sender {sender_id}", level="warning")
            return  # Skip processing if sender is not a neighbor

        updated = False
        for dest_id, (next_hop, distance) in received_table.items():
            if dest_id == self.node.node_id:
                continue  # Ignore routes to self

            # Calculate the total distance via the sender
            new_distance = self.neighbors[sender_id][1] + distance

            # Update if route to destination is shorter or destination is new
            if dest_id not in self.routing_table or new_distance < self.routing_table[dest_id][1]:
                self.routing_table[dest_id] = (sender_id, new_distance)
                updated = True
                log(self.logger, f"Node {self.node.node_id}: Updated route to {dest_id} via {sender_id} with distance {new_distance}")

        # Propagate routing table to neighbors if updates were made
        if updated:
            self.propagate_routing_table()


    def propagate_routing_table(self):
        serializable_routing_table = {str(dest): list(route) for dest, route in self.routing_table.items()}
        for neighbor_id in self.neighbors:
            try:
                requests.post(
                    f"http://127.0.0.1:{BASE_PORT + int(neighbor_id)}/receive_routing_table",
                    json=serializable_routing_table
                )
                log(self.logger, f"Node {self.node.node_id}: Sent routing table to Neighbor {neighbor_id}")
            except requests.RequestException as e:
                log(self.logger, f"Node {self.node.node_id}: Failed to send routing table to Neighbor {neighbor_id} - {e}", level="error")

    def broadcast_position(self):
        data = {"node_id": self.node.node_id, "position": self.node.position}
        for node_id in range(1, 11):
            if node_id != self.node.node_id:
                try:
                    requests.post(f"http://127.0.0.1:{BASE_PORT + node_id}/update_position", json=data)
                except requests.RequestException:
                    pass

    def start_discovery(self):
        threading.Thread(target=self._discovery_thread, daemon=True).start()

    def _discovery_thread(self):
        while True:
            self.broadcast_position()
            time.sleep(BROADCAST_INTERVAL)
