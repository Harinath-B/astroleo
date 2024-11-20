import time
import logging
import threading
import requests


class SyncManager:
    def __init__(self, node_id, get_neighbors_func):
        self.node_id = node_id
        self.local_clock = time.time()
        self.offset = 0
        self.running = False  # Control flag for the background thread
        self.sync_interval = 10  # Interval in seconds between synchronizations
        self.get_neighbors_func = get_neighbors_func  # Function to fetch neighbors

    def get_local_time(self):
        """Return the current synchronized local time."""
        return self.local_clock + self.offset

    def adjust_clock(self, adjustment):
        """Adjust the local clock by the given adjustment."""
        self.offset += adjustment

    def synchronize(self, node_times):
        """
        Synchronize with other nodes using an averaging approach.
        :param node_times: A dictionary of {node_id: local_time}.
        """
        logging.info(f"Node {self.node_id}: Starting synchronization with node times: {node_times}")

        # Include this node's time in the calculations
        node_times[self.node_id] = self.get_local_time()

        # Calculate the average time
        avg_time = sum(node_times.values()) / len(node_times)
        logging.info(f"Node {self.node_id}: Calculated average time: {avg_time}")

        # Adjust this node's clock
        adjustment = avg_time - self.get_local_time()
        self.adjust_clock(adjustment)
        logging.info(f"Node {self.node_id}: Adjusted clock by {adjustment}. New local time: {self.get_local_time()}")

        return adjustment

    def _fetch_neighbor_times(self):
        """Fetch neighbor times via Flask endpoints."""
        neighbors = self.get_neighbors_func()[0]
        neighbor_times = {}
        logging.warning(f'Neighbors {neighbors}')
        for neighbor_id in neighbors:
            neighbor_address = neighbors[neighbor_id]
            try:
                response = requests.get(f"{neighbor_address}/get_local_time")
                if response.status_code == 200:
                    neighbor_times[neighbor_id] = response.json()["local_time"]
            except requests.RequestException as e:
                logging.warning(f"Node {self.node_id}: Failed to fetch time from neighbor {neighbor_id} - {e}")
        return neighbor_times

    def _sync_loop(self):
        """Background synchronization loop."""
        while self.running:
            try:
                neighbor_times = self._fetch_neighbor_times()
                if neighbor_times:
                    self.synchronize(neighbor_times)
                else:
                    logging.warning(f"Node {self.node_id}: No neighbor times available.")
            except Exception as e:
                logging.error(f"Node {self.node_id}: Error during synchronization - {e}")
            time.sleep(self.sync_interval)

    def start(self):
        """Start the background synchronization thread."""
        self.running = True
        threading.Thread(target=self._sync_loop, daemon=True).start()
        logging.info(f"Node {self.node_id}: Started background synchronization.")

    def stop(self):
        """Stop the background synchronization thread."""
        self.running = False
        logging.info(f"Node {self.node_id}: Stopped background synchronization.")
