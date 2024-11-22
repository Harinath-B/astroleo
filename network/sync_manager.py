# network/sync_manager.py

import threading
import time
import requests

from utils.logging_utils import log

session = requests.Session()
session.trust_env = False

class SyncManager:

    def __init__(self, node, get_neighbors_func, sync_interval=5):

        self.node = node
        self.node_id = self.node.node_id
        self.get_neighbors_func = get_neighbors_func
        self.sync_interval = sync_interval  
        self.running = False  
        self.sync_thread = None  

    def _sync_loop(self):
        
        log(self.node.general_logger, f"Node {self.node_id}: Synchronization loop started.")
        while self.running:
            if self.node.state != "ACTIVE":
                continue
            try:
                log(self.node.general_logger, f"Node {self.node_id}: Fetching neighbor times for synchronization.")
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
        
        if not self.running:
            self.running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread started.")
        else:
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread is already running.")

    def stop(self):
        
        if self.running:
            self.running = False
            if self.sync_thread and self.sync_thread.is_alive():
                self.sync_thread.join(timeout=self.sync_interval + 1)
            log(self.node.general_logger, f"Node {self.node_id}: Synchronization thread stopped.")

    def synchronize(self, node_times):

        log(self.node.general_logger, f"Node {self.node_id}: Initiating Berkeley synchronization with times: {node_times}")        
        local_time = self.get_local_time()
        node_times[self.node_id] = local_time
        log(self.node.general_logger, f"Node {self.node_id}: Local time added to node_times: {node_times}")
       
        avg_time = sum(node_times.values()) / len(node_times)
        log(self.node.general_logger, f"Node {self.node_id}: Average time calculated: {avg_time}")        
        time_adjustments = {node_id: avg_time - time for node_id, time in node_times.items()}
        log(self.node.general_logger, f"Node {self.node_id}: Time adjustments calculated: {time_adjustments}")        
        adjustment = time_adjustments[self.node_id]
        self.adjust_clock(adjustment)
        log(self.node.general_logger, f"Node {self.node_id}: Adjusted local clock by {adjustment}. New local time: {self.get_local_time()}")
        
        return adjustment


    def _fetch_neighbor_times(self):
        
        neighbors = self.get_neighbors_func()[0]
        neighbor_times = {}
        log(self.node.general_logger, f"Node {self.node_id} neigbors {neighbors}")
        for neighbor_id in neighbors:
            neighbor_address = neighbors[neighbor_id]
            try:
                response = session.get(f"{neighbor_address}/get_local_time", timeout=5)
                if response.status_code == 200:
                    neighbor_times[neighbor_id] = response.json()["local_time"]
                else:
                    log(self.node.general_logger, f"Node {self.node_id}: Failed to fetch time from neighbor {neighbor_id}.")

            except requests.RequestException as e:
                log(self.node.general_logger, f"Node {self.node_id}: Error fetching time from neighbor {neighbor_id} - {e}")

        return neighbor_times

    def get_local_time(self):
        
        return time.time()

    def adjust_clock(self, adjustment):
        
        log(self.node.general_logger, f"Node {self.node_id}: Adjusting clock by {adjustment} seconds.")
