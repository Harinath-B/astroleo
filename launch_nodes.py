import subprocess
import time
import random
import json
import os
import threading
import requests
from app.config import NUM_NODES, POSITIONS_FILE

def generate_positions(num_nodes):
    positions = {node_id: (round(random.uniform(0, 10), 2),
                           round(random.uniform(0, 10), 2),
                           round(random.uniform(0, 10), 2))
                 for node_id in range(1, num_nodes + 1)}
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)
    return positions

def simulate_failures(num_nodes, failure_interval=15, recovery_interval=15):
    """
    Randomly simulate node failures and recoveries.
    """
    while True:
        # Randomly pick a node to fail
        failed_node = random.randint(1, num_nodes)
        print(f"Simulating failure for Node {failed_node}")
        try:
            response = requests.post(f"http://127.0.0.1:{5000 + failed_node}/fail")
            if response.status_code == 200:
                print(f"Node {failed_node} failed.")
            else:
                print(f"Failed to mark Node {failed_node} as FAILED: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error failing Node {failed_node}: {e}")

        # Wait for a recovery interval
        time.sleep(random.randint(failure_interval, recovery_interval))

        # Recover the node
        print(f"Recovering Node {failed_node}")
        try:
            response = requests.post(f"http://127.0.0.1:{5000 + failed_node}/recover")
            if response.status_code == 200:
                print(f"Node {failed_node} recovered.")
            else:
                print(f"Failed to recover Node {failed_node}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error recovering Node {failed_node}: {e}")

        # Wait for the next failure interval
        time.sleep(failure_interval)

def launch_nodes(num_nodes=NUM_NODES):
    positions = generate_positions(num_nodes)
    os.makedirs("logs", exist_ok=True)
    processes = []

    try:
        for node_id, position in positions.items():
            x, y, z = position
            cmd = ["python", "main.py", str(node_id), str(x), str(y), str(z), str(0)]
            log_file_path = f"logs/node_{node_id}.log"
            with open(log_file_path, "w") as log_file:
                process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
                processes.append(process)
            
            print(f"Launching Node {node_id} at position {position}")
            time.sleep(0.5)
            
        time.sleep(1)

        # Start the failure simulation thread
        failure_thread = threading.Thread(target=simulate_failures, args=(num_nodes,))
        failure_thread.daemon = True
        failure_thread.start()

        # Keep the script running to allow failure simulation
        while True:
            time.sleep(1)

    except Exception as e:
        print(f"Error launching nodes: {e}")
    finally:
        for process in processes:
            process.terminate()
        print("All nodes terminated.")

if __name__ == "__main__":
    launch_nodes()
