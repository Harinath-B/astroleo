import threading
import time
import logging
import requests
from utils.logging_utils import log

class SyncManager:
    def __init__(self, node, get_neighbors_func, sync_interval=5):
        self.node = node
        self.node_id = self.node.node_id
        self.get_neighbors_func = get_neighbors_func
        self.sync_interval = sync_interval  # Interval for synchronization in seconds
        self.running = False  # Flag to indicate whether the loop is active
        self.sync_thread = None  # Reference to the synchronization thread

    def _sync_loop(self):
        """Periodic synchronization loop to adjust local clock."""
        log(self.node.general_logger, f"Node {self.node_id}: Synchronization loop started.")
        while self.running:
            if self.node.state != "ACTIVE":
                continue
            try:
                logging.debug(f"Node {self.node_id}: Fetching neighbor times for synchronization.")
                neighbor_times = self._fetch_neighbor_times()
                
                if neighbor_times:
                    adjustment = self.synchronize(neighbor_times)
                    log(self.node.general_logger, f"Node {self.node_id}: Synchronized with adjustment: {adjustment}")
                else:
                    log(self.node.general_logger, f"Node {self.node_id}: No neighbors available for synchronization.")

            except Exception as e:
                log(self.node.general_logger, f"Node {self.node_id}: Error during synchronization - {e}", level='error')
            
            time.sleep(self.sync_interval)

        log(self.node.general_logger, f"Node {self.node_id}: Synchronization loop stopped.")

    def start(self):
        """Start the synchronization thread."""
        if not self.running:
            self.running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread started.")
        else:
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread is already running.")

    def stop(self):
        """Stop the synchronization thread."""
        if self.running:
            self.running = False
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=self.sync_interval + 1)
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread stopped.")

    def synchronize(self, node_times):

        log(self.node.general_logger, f"Node {self.node_id}: Initiating Berkeley synchronization with times: {node_times}")

        # Add the local time to the node times
        local_time = self.get_local_time()
        node_times[self.node_id] = local_time
        log(self.node.general_logger, f"Node {self.node_id}: Local time added to node_times: {node_times}")

        # Calculate the average time
        avg_time = sum(node_times.values()) / len(node_times)
        log(self.node.general_logger, f"Node {self.node_id}: Average time calculated: {avg_time}")

        # Compute the adjustments for each node
        time_adjustments = {node_id: avg_time - time for node_id, time in node_times.items()}
        log(self.node.general_logger, f"Node {self.node_id}: Time adjustments calculated: {time_adjustments}")

        # Apply the adjustment to the local clock
        adjustment = time_adjustments[self.node_id]
        self.adjust_clock(adjustment)
        log(self.node.general_logger, f"Node {self.node_id}: Adjusted local clock by {adjustment}. New local time: {self.get_local_time()}")

        # Return only the adjustment for this node
        return adjustment


    def _fetch_neighbor_times(self):
        """Fetch local times from all neighbors."""
        neighbors = self.get_neighbors_func()[0]
        neighbor_times = {}
        log(self.node.general_logger, f"Node {self.node_id} neigbors {neighbors}")
        for neighbor_id in neighbors:
            neighbor_address = neighbors[neighbor_id]
            try:
                response = requests.get(f"{neighbor_address}/get_local_time", timeout=5)
                if response.status_code == 200:
                    neighbor_times[neighbor_id] = response.json()["local_time"]
                else:
                    logging.warning(f"Node {self.node_id}: Failed to fetch time from neighbor {neighbor_id}.")
            except requests.RequestException as e:
                logging.warning(f"Node {self.node_id}: Error fetching time from neighbor {neighbor_id} - {e}")
        return neighbor_times

    def get_local_time(self):
        """Simulate fetching the node's local time."""
        return time.time()

    def adjust_clock(self, adjustment):
        """Simulate adjusting the node's clock."""
        log(self.node.general_logger, f"Node {self.node_id}: Adjusting clock by {adjustment} seconds.")
