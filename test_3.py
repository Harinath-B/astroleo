import requests
import json

from app.config import BASE_PORT, POSITIONS_FILE

session = requests.Session()
session.trust_env = False

with open(POSITIONS_FILE, "r") as file:
    positions = json.load(file)

def print_routing_tables():
    
    print("\nRouting Tables of All Nodes:")
    for node_id in positions:
        try:
            url = f"http://10.35.70.23:{BASE_PORT + int(node_id)}/get_routing_table"
            response = session.get(url)
            if response.status_code == 200:
                routing_table = response.json()
                print(f"Node {node_id} Routing Table:")
                for dest, route_info in routing_table.items():
                    print(f"  Destination: {dest}, Route Info: {route_info}")
            else:
                print(f"Node {node_id}: Failed to retrieve routing table. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error querying Node {node_id}: {e}")

def test_discovery():
    
    print("\n=== Discovery Test ===")
    print_routing_tables()

def test_routing(source_id, dest_id, payload):
    
    print(f"\n=== Routing Test: Sending message from Node {source_id} to Node {dest_id} ===")
    url = f"http://10.35.70.23:{BASE_PORT + source_id}/send"
    response = session.post(url, json={"dest_id": dest_id, "payload": payload})
    if response.status_code == 200:
        print(f"Routing Test Successful: {response.json()}")
    else:
        print(f"Routing Test Failed: {response.status_code} - {response.text}")

def test_encryption_decryption(source_id, dest_id, payload):
    
    print(f"\n=== Encryption and Decryption Test: Sending encrypted message from Node {source_id} to Node {dest_id} ===")
    send_url = f"http://10.35.70.23:{BASE_PORT + source_id}/send"
    response = session.post(send_url, json={"dest_id": dest_id, "payload": payload})

    if response.status_code == 200:
        print(f"Encryption Test Successful: {response.json()}")
    else:
        print(f"Encryption Test Failed: {response.status_code} - {response.text}")
    
    print("\nValidating decryption at the destination node...")
    get_last_received_url = f"http://10.35.70.23:{BASE_PORT + dest_id}/get_last_received_packet"
    dest_response = session.get(get_last_received_url)

    if dest_response.status_code == 200:
        response_data = dest_response.json()
        if response_data == payload:
            print("Decryption Verified: Message matches the original payload.")
        else:
            print("Decryption Failed: Received message does not match the original payload.")
    else:
        print(f"Failed to query /get_last_received_packet endpoint for Node {dest_id}: {dest_response.status_code} - {dest_response.text}")

if __name__ == "__main__":
    
    print("=== Step 1: Discovery Test ===")
    test_discovery()
    
    print("\n=== Step 2: Routing Test ===")
    source_node = 2
    destination_node = 3
    test_routing(source_node, destination_node, "Hello from Node 1!")
    
    print("\n=== Step 3: Encryption and Decryption Test ===")
    test_encryption_decryption(source_node, destination_node, "Encrypted message from Node 1!")
