import time
import random
import requests
import threading
import subprocess
import json
import os
import base64

from app.satellite_node import SatelliteNode
from app.config import NUM_NODES, POSITIONS_FILE
from utils.logging_utils import setup_logger, log

session = requests.Session()
session.trust_env = False

logger = setup_logger(node_id=0, log_type="demo_presentation")

class SatelliteDemo:

    def __init__(self, num_nodes=5):

        self.num_nodes = num_nodes
        self.processes = []
        self.satellites = {}
        self.running = True

    def generate_positions(self):
        
        positions = {
            node_id: (
                round(random.uniform(0, 10), 2),
                round(random.uniform(0, 10), 2),
                round(random.uniform(0, 10), 2)
            ) for node_id in range(1, self.num_nodes + 1)
        }
        with open(POSITIONS_FILE, 'w') as f:
            json.dump(positions, f)
        return positions

    def launch_nodes(self):
        
        positions = self.generate_positions()
        os.makedirs("logs", exist_ok=True)
        
        log(logger, "Launching satellite nodes...", level="info")
        for node_id, position in positions.items():
            x, y, z = position
            cmd = ["python", "main.py", str(node_id), str(x), str(y), str(z)]
            log_file_path = f"logs/node_{node_id}.log"            
            with open(log_file_path, "w") as log_file:
                process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
                self.processes.append(process)
                        
            self.satellites[node_id] = SatelliteNode(node_id=node_id, position=position)
            log(logger, f"Launched Node {node_id} at position {position}", level="info")
            time.sleep(0.5)  

    def simulate_failures_and_recovery(self):
        
        while self.running:
            failed_node = random.randint(1, self.num_nodes)
            log(logger, f"Simulating failure for Node {failed_node}", level="warning")            
            try:
                response = session.post(f"http://10.35.70.23:{5000 + failed_node}/fail")
                if response.status_code == 200:
                    log(logger, f"Node {failed_node} failed.", level="error")
                else:
                    log(logger, f"Failed to mark Node {failed_node} as FAILED: {response.status_code}", level="error")

            except requests.RequestException as e:
                log(logger, f"Error failing Node {failed_node}: {e}", level="error")

            time.sleep(10)  

            try:
                response = session.post(f"http://10.35.70.23:{5000 + failed_node}/recover")
                if response.status_code == 200:
                    log(logger, f"Node {failed_node} recovered.", level="info")
                else:
                    log(logger, f"Failed to recover Node {failed_node}: {response.status_code}", level="error")

            except requests.RequestException as e:
                log(logger, f"Error recovering Node {failed_node}: {e}", level="error")
            time.sleep(10)  

    def test_encryption_and_decryption(self, source_node_id, target_node_id):
        
        log(logger, f"Testing encryption and decryption between Node {source_node_id} and Node {target_node_id}", level="info")        
        try:            
            source_encryption_manager = self.satellites[source_node_id].encryption_manager
            target_encryption_manager = self.satellites[target_node_id].encryption_manager
            source_public_key = source_encryption_manager.get_public_key()
            target_public_key = target_encryption_manager.get_public_key()
            
            source_shared_key = source_encryption_manager.generate_shared_secret(
                base64.b64decode(target_public_key)
            )
            target_shared_key = target_encryption_manager.generate_shared_secret(
                base64.b64decode(source_public_key)
            )

            test_message = "This is a secure test message."            
            encrypted_message = source_encryption_manager.encrypt(test_message, source_shared_key)
            log(logger, f"Encrypted Message: {encrypted_message}", level="info")            
            decrypted_message = target_encryption_manager.decrypt(encrypted_message, target_shared_key).decode()
            log(logger, f"Decrypted Message: {decrypted_message}", level="info")
            
            assert test_message == decrypted_message
            log(logger, "Encryption and decryption test successful!", level="success")

        except Exception as e:
            log(logger, f"Error during encryption and decryption test: {e}", level="error")

    def test_capture_and_transmit_image(self, source_node_id, dest_node_id):
        
        log(logger, f"Testing capture and transmit image from Node {source_node_id} to Node {dest_node_id}", level="info")        
        try:
            
            capture_response = session.post(f"http://10.35.70.23:{5000 + source_node_id}/capture_image")
            if capture_response.status_code == 200:
                image_path = capture_response.json().get("image_path")
                log(logger, f"Image captured successfully by Node {source_node_id}: {image_path}", level="info")
                                
                transmit_response = session.post(
                    f"http://10.35.70.23:{5000 + source_node_id}/transmit_image",
                    json={"dest_id": dest_node_id, "image_path": image_path}
                )
                if transmit_response.status_code == 200:
                    log(logger, f"Image successfully transmitted from Node {source_node_id} to Node {dest_node_id}.", level="info")
                else:
                    log(logger, f"Image transmission failed: {transmit_response.status_code}", level="error")
            else:
                log(logger, f"Image capture failed for Node {source_node_id}: {capture_response.status_code}", level="error")

        except requests.RequestException as e:
            log(logger, f"Error during capture and transmit image from Node {source_node_id}: {e}", level="error")

    def test_packet_transmission(self, source_node_id, dest_node_id):
        
        log(logger, f"Testing packet transmission from Node {source_node_id} to Node {dest_node_id}", level="info")
        
        try:
            response = session.post(
                f"http://10.35.70.23:{5000 + source_node_id}/send",
                json={"dest_id": dest_node_id, "payload": "Test packet message"}
            )
            if response.status_code == 200:
                log(logger, f"Packet successfully sent from Node {source_node_id} to Node {dest_node_id}.", level="info")
            else:
                log(logger, f"Packet transmission failed: {response.status_code}", level="error")

        except requests.RequestException as e:
            log(logger, f"Error during packet transmission from Node {source_node_id}: {e}", level="error")

    def test_heartbeat(self, node_id):
        
        log(logger, f"Testing heartbeat for Node {node_id}", level="info")
        timestamp = time.time()
        data = {"node_id": node_id, "timestamp": timestamp}
        
        try:
            response = session.post(f"http://10.35.70.23:{5000 + node_id}/heartbeat", json=data)
            if response.status_code == 200:
                log(logger, f"Heartbeat sent from Node {node_id} successfully.", level="info")
            else:
                log(logger, f"Failed to send heartbeat from Node {node_id}. Status code: {response.status_code}", level="error")

        except requests.RequestException as e:
            log(logger, f"Error sending heartbeat for Node {node_id}: {e}", level="error")

    def run_tests(self):
        
        log(logger, "Starting continuous satellite network tests...", level="info")       
        while self.running:
            for node_id in range(1, self.num_nodes + 1):
                target_node_id = random.randint(1, self.num_nodes)
                while target_node_id == node_id:
                    target_node_id = random.randint(1, self.num_nodes)
                
                try:
                    self.test_encryption_and_decryption(node_id, target_node_id)
                    self.test_capture_and_transmit_image(node_id, target_node_id)
                    self.test_packet_transmission(node_id, target_node_id)
                    self.test_heartbeat(node_id)

                except requests.RequestException as e:
                    log(logger, f"Error during tests for Node {node_id}: {e}", level="error")
                time.sleep(1)

    def cleanup(self):
        
        self.running = False
        for process in self.processes:
            process.terminate()
        log(logger, "Cleaned up all node processes", level="info")

def main():
    demo = SatelliteDemo(num_nodes=5)
    
    try:
        demo.launch_nodes()
        time.sleep(2)
        failure_thread = threading.Thread(target=demo.simulate_failures_and_recovery)
        failure_thread.daemon = True
        failure_thread.start()
        demo.run_tests()

    except KeyboardInterrupt:
        log(logger, "Demo stopped by user", level="info")

    except Exception as e:
        log(logger, f"Error during demo: {e}", level="error")

    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()
