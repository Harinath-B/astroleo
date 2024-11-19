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
        self.heartbeat_interval = 5  # Interval to send heartbeats (seconds)
        self.heartbeat_timeout = 15  # Timeout to consider a neighbor inactive (seconds)
        self.last_heartbeat = {}  # Track last received heartbeat from neighbors

    def send_heartbeat(self):
        """
        Send heartbeat packets to all neighbors.
        """
        for neighbor_id in self.neighbors:
            try:
                requests.post(
                    f"http://127.0.0.1:{BASE_PORT + int(neighbor_id)}/heartbeat",
                    json={"node_id": self.node.node_id, "timestamp": time.time()},
                )
                log(self.node.general_logger, f"Sent heartbeat to Node {neighbor_id}")
            except requests.RequestException:
                log(self.node.general_logger, f"Failed to send heartbeat to Node {neighbor_id}", level="error")

    def receive_heartbeat(self, sender_id, timestamp):
        """
        Handle a received heartbeat packet.
        """
        self.last_heartbeat[sender_id] = timestamp
        log(self.node.general_logger, f"Received heartbeat from Node {sender_id}")

    def monitor_neighbors(self):
        """
        Monitor neighbors' health by checking the last heartbeat timestamp.
        """
        while True:
            current_time = time.time()
            for neighbor_id, last_time in list(self.last_heartbeat.items()):
                if current_time - last_time > self.heartbeat_timeout:
                    log(self.node.general_logger, f"Node {neighbor_id} is unreachable", level="warning")
                    self.remove_neighbor(neighbor_id)
            time.sleep(self.heartbeat_interval)

    def remove_neighbor(self, neighbor_id):
        """
        Remove a neighbor from the neighbors list and update routing table.
        """
        if neighbor_id in self.neighbors:
            del self.neighbors[neighbor_id]
            del self.last_heartbeat[neighbor_id]
            log(self.node.general_logger, f"Removed neighbor {neighbor_id}")
        self.routing_table.pop(neighbor_id, None)

    def start_heartbeat(self):
        """
        Start sending heartbeats and monitoring neighbors.
        """
        threading.Thread(target=self._heartbeat_thread, daemon=True).start()
        threading.Thread(target=self.monitor_neighbors, daemon=True).start()

    def _heartbeat_thread(self):
        """
        Periodically send heartbeats.
        """
        while True:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)

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
