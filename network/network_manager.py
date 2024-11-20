import requests
import time
import threading
from math import cos, sin, radians
from app.config import DISCOVERY_RANGE, BROADCAST_INTERVAL, BASE_PORT
from utils.logging_utils import log, setup_logger
from utils.distance_utils import calculate_distance
from network.packet import Packet
import json

class NetworkManager:
    def __init__(self, node):
        self.node = node
        self.neighbors = {}
        self.routing_table = {}
        self.logger = setup_logger(self.node.node_id, "general")
        self.heartbeat_interval = 5  # Interval to send heartbeats (seconds)
        self.heartbeat_timeout = 7  # Timeout to consider a neighbor inactive (seconds)
        self.last_heartbeat = {}  # Track last received heartbeat from neighbors
        self.position_update_interval = 10  # Position update interval (seconds)

    def start(self):
        """
        Start all necessary threads for dynamic position updates, discovery, and heartbeats.
        """
        threading.Thread(target=self._heartbeat_thread, daemon=True).start()
        threading.Thread(target=self.monitor_neighbors, daemon=True).start()
        threading.Thread(target=self._position_update_thread, daemon=True).start()
        threading.Thread(target=self._discovery_thread, daemon=True).start()

    def _position_update_thread(self):
        """
        Periodically update the node's position based on a mobility model.
        """
        while True:
            if self.node.is_active():
                self.update_position()
                self.broadcast_position()
            time.sleep(self.position_update_interval)

    def update_position(self):
        """
        Simulate position updates using a circular orbital model.
        """
        t = time.time()  # Current time
        radius = 5  # Example orbital radius
        speed = 0.01  # Angular velocity (radians/second)
        center_x, center_y = 5, 5  # Orbital center

        new_x = center_x + radius * cos(speed * t)
        new_y = center_y + radius * sin(speed * t)
        self.node.position = (new_x, new_y, self.node.position[2])
        log(self.logger, f"Updated position to {self.node.position}")

    def broadcast_position(self):
        """
        Broadcast the updated position to all nodes in the network.
        """
        if not self.node.is_active():
            return

        data = {"node_id": self.node.node_id, "position": self.node.position}
        for node_id in range(1, 11):  # Assuming up to 10 nodes
            if node_id != self.node.node_id:
                try:
                    requests.post(
                        f"http://127.0.0.1:{BASE_PORT + node_id}/update_position",
                        json=data,
                    )
                except requests.RequestException:
                    pass

    def update_position_with_neighbor(self, neighbor_id, position):
        """
        Handle position updates from a neighbor.
        """
        distance = calculate_distance(self.node.position, position)
        if distance <= DISCOVERY_RANGE:
            self.neighbors[neighbor_id] = (position, distance)
            self.routing_table[neighbor_id] = (neighbor_id, distance)
            log(self.logger, f"Node {self.node.node_id}: Added direct neighbor {neighbor_id} with distance {distance}")
            self.broadcast_public_key()
            self.propagate_routing_table()

    def send_heartbeat(self):
        """
        Send heartbeat packets to all neighbors.
        """
        if not self.node.is_active():
            return

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
            if self.node.is_active():
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

    def broadcast_public_key(self):
        """
        Broadcast this node's public key to all neighbors.
        """
        if not self.node.is_active():
            return

        public_key = self.node.encryption_manager.get_public_key()
        for neighbor_id in self.neighbors:
            try:
                neighbor_address = self.get_neighbor_address(neighbor_id)
                if neighbor_address:
                    requests.post(
                        f"{neighbor_address}/exchange_key",
                        json={"node_id": self.node.node_id, "public_key": public_key},
                    )
                    log(self.logger, f"Broadcasted public key to Node {neighbor_id}")
            except Exception as e:
                log(self.logger, f"Failed to broadcast public key to Node {neighbor_id}: {e}", level="error")

    def get_neighbor_addresses(self):
        """Retrieve the list of active neighbors and their details."""
        if not self.node.is_active():
            return json.dumps({"error": "Node is offline"}), 400

        neighbors = self.neighbors
        response = dict()
        for neighbor_id in neighbors.keys():
            response[neighbor_id] = self.get_neighbor_address(neighbor_id)
        # response = {
        #     neighbor_id: self.get_neighbor_address(neighbor_id)
        #     for neighbor_id in neighbors.keys()
        # }
        return response, 200
    
    def get_neighbor_address(self, neighbor_id):
        """
        Get the HTTP address of a neighbor.
        """
        return f"http://127.0.0.1:{5000 + neighbor_id}"

    def update_routing_table(self, received_table, sender_id):
        """
        Update routing table based on a received routing table from a neighbor.
        """
        if sender_id not in self.neighbors:
            log(self.logger, f"Received routing table from unknown sender {sender_id}", level="warning")
            return

        updated = False
        for dest_id, (next_hop, distance) in received_table.items():
            if dest_id == self.node.node_id:
                continue

            new_distance = self.neighbors[sender_id][1] + distance
            if dest_id not in self.routing_table or new_distance < self.routing_table[dest_id][1]:
                self.routing_table[dest_id] = (sender_id, new_distance)
                updated = True
                log(self.logger, f"Updated route to {dest_id} via {sender_id} with distance {new_distance}")

        if updated:
            self.propagate_routing_table()

    def propagate_routing_table(self):
        """
        Propagate the routing table to all neighbors.
        """
        if not self.node.is_active():
            return

        serializable_routing_table = {str(dest): list(route) for dest, route in self.routing_table.items()}
        for neighbor_id in self.neighbors:
            try:
                requests.post(
                    f"http://127.0.0.1:{BASE_PORT + int(neighbor_id)}/receive_routing_table",
                    json=serializable_routing_table,
                )
                log(self.logger, f"Sent routing table to Neighbor {neighbor_id}")
            except requests.RequestException as e:
                log(self.logger, f"Failed to send routing table to Neighbor {neighbor_id} - {e}", level="error")

    def _heartbeat_thread(self):
        """
        Periodically send heartbeats.
        """
        while True:
            if self.node.is_active():
                self.send_heartbeat()
            time.sleep(self.heartbeat_interval)

    def _discovery_thread(self):
        """
        Periodically broadcast positions for discovery.
        """
        while True:
            if self.node.is_active():
                self.broadcast_position()
            time.sleep(BROADCAST_INTERVAL)
