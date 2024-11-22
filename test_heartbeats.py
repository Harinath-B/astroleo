import requests
import time
import json

from app.config import BASE_PORT

session = requests.Session()
session.trust_env = False

def load_positions_from_json(json_file):

    with open(json_file, 'r') as f:
        positions = json.load(f)
    return {int(node_id): tuple(position) for node_id, position in positions.items()}

def test_heartbeats_with_json(json_file):
    
    positions = load_positions_from_json(json_file)    
    print("Waiting for heartbeats...")
    time.sleep(20)
   
    for node_id in positions:
        response = session.get(f"http://10.35.70.23:{BASE_PORT + node_id}/get_neighbors")
        print(f"Node {node_id} neighbors: {response.json()}")

if __name__ == "__main__":
    test_heartbeats_with_json("positions.json")
