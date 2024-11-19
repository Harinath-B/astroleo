# launch_nodes.py

import subprocess
import time
import random
import json
import os
from app.config import NUM_NODES, POSITIONS_FILE

def generate_positions(num_nodes):
    positions = {node_id: (round(random.uniform(0, 10), 2),
                           round(random.uniform(0, 10), 2),
                           round(random.uniform(0, 10), 2))
                 for node_id in range(1, num_nodes + 1)}
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)
    return positions

def launch_nodes(num_nodes=NUM_NODES):
    positions = generate_positions(num_nodes)
    os.makedirs("logs", exist_ok=True)
    processes = []

    try:
        for node_id, position in positions.items():
            x, y, z = position
            cmd = ["python", "main.py", str(node_id), str(x), str(y), str(z)]
            log_file_path = f"logs/node_{node_id}.log"
            with open(log_file_path, "w") as log_file:
                process = subprocess.Popen(cmd, stdout=log_file, stderr=log_file)
                processes.append(process)
            
            print(f"Launching Node {node_id} at position {position}")
            time.sleep(0.5)
    except Exception as e:
        print(f"Error launching nodes: {e}")
    finally:
        for process in processes:
            process.wait()
        print("All nodes terminated.")

if __name__ == "__main__":
    launch_nodes()
