import requests
import time
import json
import os

session = requests.Session()
session.trust_env = False

def load_positions_from_json(json_file):
    """Load satellite positions from a JSON file."""
    with open(json_file, 'r') as f:
        positions = json.load(f)
    return {int(node_id): tuple(position) for node_id, position in positions.items()}


BASE_PORT = 5000  # Base port for nodes

def test_heartbeats_with_json(json_file):
    """
    Test the heartbeat system using node positions loaded from a JSON file.
    """
    # Load positions from JSON
    positions = load_positions_from_json(json_file)

    # Initialize nodes with positions

    # Allow time for nodes to exchange heartbeats
    print("Waiting for heartbeats...")
    time.sleep(20)

    # Check neighbors for each node
    for node_id in positions:
        response = session.get(f"http://10.35.70.23:{BASE_PORT + node_id}/get_neighbors")
        print(f"Node {node_id} neighbors: {response.json()}")

# Run the test
if __name__ == "__main__":
    test_heartbeats_with_json("positions.json")
2