import subprocess
import time
import requests
import random

def launch_satellite(node_id, x, y, z):
    """Launch a single satellite node."""
    cmd = ["python", "main.py", str(node_id), str(x), str(y), str(z), "0"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_local_time(node_id):
    """Fetch the local time of a satellite node."""
    url = f"http://127.0.0.1:{5000 + node_id}/get_local_time"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()["local_time"]
        else:
            print(f"Failed to fetch time for Node {node_id}: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error fetching time from Node {node_id}: {e}")
    return None

def synchronize_time(node_id, neighbor_times):
    """Send time synchronization data to a satellite node."""
    url = f"http://127.0.0.1:{5000 + node_id}/synchronize_time"
    try:
        response = requests.post(url, json={"neighbor_times": neighbor_times}, timeout=5)
        if response.status_code == 200:
            print(f"Node {node_id} synchronized successfully.")
        else:
            print(f"Failed to synchronize Node {node_id}: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error synchronizing Node {node_id}: {e}")

def main():
    """Main function to launch satellites and test synchronization."""
    num_nodes = 5
    processes = []
    nodes = []

    # Launch satellite nodes
    for node_id in range(1, num_nodes + 1):
        x, y, z = random.uniform(0, 10), random.uniform(0, 10), random.uniform(0, 10)
        print(f"Launching Node {node_id} at position ({x}, {y}, {z})")
        process = launch_satellite(node_id, x, y, z)
        processes.append(process)
        nodes.append(node_id)
        time.sleep(1)  # Small delay to ensure nodes start up

    # Wait for nodes to initialize
    print("Waiting for nodes to initialize...")
    time.sleep(10)

    # Fetch initial times
    initial_times = {}
    for node_id in nodes:
        time_value = get_local_time(node_id)
        if time_value:
            initial_times[node_id] = time_value
            print(f"Node {node_id} initial time: {time_value}")
        else:
            print(f"Failed to fetch initial time for Node {node_id}")

    # Synchronize times
    print("Synchronizing times...")
    for node_id in nodes:
        synchronize_time(node_id, initial_times)

    # Wait for synchronization to complete
    time.sleep(5)

    # Fetch synchronized times
    synchronized_times = {}
    for node_id in nodes:
        time_value = get_local_time(node_id)
        if time_value:
            synchronized_times[node_id] = time_value
            print(f"Node {node_id} synchronized time: {time_value}")
        else:
            print(f"Failed to fetch synchronized time for Node {node_id}")

    # Calculate synchronization difference
    print("Synchronization results:")
    for node_id in nodes:
        initial_time = initial_times.get(node_id)
        synchronized_time = synchronized_times.get(node_id)
        if initial_time and synchronized_time:
            print(f"Node {node_id}: Adjustment = {synchronized_time - initial_time}")

    # Terminate processes
    for process in processes:
        process.terminate()
    print("All nodes terminated.")

if __name__ == "__main__":
    main()
