import requests
import json
import time
import random
from config import BASE_PORT, DISCOVERY_RANGE, BROADCAST_INTERVAL

NUM_NODES = 10
POSITIONS_FILE = "positions.json"
MESSAGE = "Hello from Node"
SLEEP_INTERVAL = 2
LONG_DELAY = 2

def generate_positions(num_nodes):
    """Generate random positions for nodes."""
    return {node_id: (round(random.uniform(0, 10), 2),
                      round(random.uniform(0, 10), 2),
                      round(random.uniform(0, 10), 2))
            for node_id in range(1, num_nodes + 1)}

def save_positions(positions):
    """Save generated positions to a JSON file."""
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(positions, f)

def load_positions():
    """Load positions from the saved JSON file."""
    with open(POSITIONS_FILE, 'r') as f:
        return json.load(f)

def initialize_nodes(positions):
    """Initialize nodes with positions by posting to their update_position endpoint."""
    print("Initializing nodes with positions...")
    for node_id, position in positions.items():
        try:
            requests.post(
                f"http://127.0.0.1:{BASE_PORT + int(node_id)}/update_position", 
                json={"node_id": node_id, "position": position}
            )
            print(f"Node {node_id} initialized at position {position}")
        except requests.RequestException as e:
            print(f"Failed to initialize Node {node_id}: {e}")
    time.sleep(SLEEP_INTERVAL)

def check_routing_tables():
    """Retrieve and display routing tables for each node."""
    print("\nChecking routing tables...")
    for node_id in range(1, NUM_NODES + 1):
        try:
            response = requests.get(f"http://127.0.0.1:{BASE_PORT + int(node_id)}/get_routing_table")
            if response.status_code == 200:
                routing_table = response.json()
                print(f"Routing table for Node {node_id}: {routing_table}")
            else:
                print(f"Failed to retrieve routing table for Node {node_id}")
        except requests.RequestException as e:
            print(f"Error retrieving routing table for Node {node_id}: {e}")

def send_message(src_id, dest_id, payload):
    """Send a message from one node to another."""
    try:
        response = requests.post(
            f"http://127.0.0.1:{BASE_PORT + int(src_id)}/send",
            json={"dest_id": dest_id, "payload": payload}
        )
        print(f"Message from Node {src_id} to Node {dest_id}: {response.json()}")
    except requests.RequestException as e:
        print(f"Failed to send message from Node {src_id} to Node {dest_id}: {e}")

def main():
    # Step 1: Generate and save positions
    positions = load_positions()
    # save_positions(positions)

    # Step 2: Initialize nodes with positions
    initialize_nodes(positions)

    # Step 3: Wait for initial discovery and routing tables to propagate
    print("\nWaiting for routing tables to propagate...")
    time.sleep(LONG_DELAY)

    # Step 4: Check routing tables to confirm discovery and routing updates
    check_routing_tables()

    # Step 5: Test message sending
    print("\nTesting message routing...")
    # Example: Send messages between random nodes, including nodes not directly reachable
    send_message(1, 3, f"{MESSAGE} 1 to 3!")
    send_message(2, 4, f"{MESSAGE} 2 to 4!")
    send_message(5, 9, f"{MESSAGE} 5 to 9!")
    send_message(3, 10, f"{MESSAGE} 3 to 10!")
    send_message(6, 7, f"{MESSAGE} 6 to 7!")

    # Wait for routing tables to potentially update with new routes
    print("\nWaiting for on-demand routing to complete...")
    time.sleep(LONG_DELAY)

    # Step 6: Check routing tables again to observe updates
    print("\nRechecking routing tables after on-demand routing...")
    check_routing_tables()

if __name__ == "__main__":
    main()
