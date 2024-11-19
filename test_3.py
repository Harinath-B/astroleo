import requests
import json
import time

# Configuration
BASE_PORT = 5000
POSITIONS_FILE = "positions.json"

# Load positions from positions.json
with open(POSITIONS_FILE, "r") as file:
    positions = json.load(file)

def print_routing_tables():
    """
    Query and print the routing tables of all nodes.
    """
    print("\nRouting Tables of All Nodes:")
    for node_id in positions:
        try:
            url = f"http://127.0.0.1:{BASE_PORT + int(node_id)}/get_routing_table"
            response = requests.get(url)
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
    """
    Test the discovery functionality by printing routing tables of all nodes.
    """
    print("\n=== Discovery Test ===")
    print_routing_tables()

def test_routing(source_id, dest_id, payload):
    """
    Test routing by sending a message from one node to another.
    """
    print(f"\n=== Routing Test: Sending message from Node {source_id} to Node {dest_id} ===")
    url = f"http://127.0.0.1:{BASE_PORT + source_id}/send"
    response = requests.post(url, json={"dest_id": dest_id, "payload": payload})
    if response.status_code == 200:
        print(f"Routing Test Successful: {response.json()}")
    else:
        print(f"Routing Test Failed: {response.status_code} - {response.text}")

def test_encryption_decryption(source_id, dest_id, payload):
    """
    Test encryption by ensuring payload encryption and decryption work correctly.
    """
    print(f"\n=== Encryption and Decryption Test: Sending encrypted message from Node {source_id} to Node {dest_id} ===")
    send_url = f"http://127.0.0.1:{BASE_PORT + source_id}/send"
    response = requests.post(send_url, json={"dest_id": dest_id, "payload": payload})

    if response.status_code == 200:
        print(f"Encryption Test Successful: {response.json()}")
    else:
        print(f"Encryption Test Failed: {response.status_code} - {response.text}")

    # Query the destination node to verify the last received packet
    print("\nValidating decryption at the destination node...")
    get_last_received_url = f"http://127.0.0.1:{BASE_PORT + dest_id}/get_last_received_packet"
    dest_response = requests.get(get_last_received_url)

    if dest_response.status_code == 200:
        response_data = dest_response.json()
        if response_data.get("decrypted_payload") == payload:
            print("Decryption Verified: Message matches the original payload.")
        else:
            print("Decryption Failed: Received message does not match the original payload.")
    else:
        print(f"Failed to query /get_last_received_packet endpoint for Node {dest_id}: {dest_response.status_code} - {dest_response.text}")



if __name__ == "__main__":
    # Step 1: Discovery Test
    print("=== Step 1: Discovery Test ===")
    test_discovery()

    # Step 2: Routing Test
    print("\n=== Step 2: Routing Test ===")
    source_node = 1
    destination_node = 3
    test_routing(source_node, destination_node, "Hello from Node 1!")

    # Step 3: Encryption and Decryption Test
    print("\n=== Step 3: Encryption and Decryption Test ===")
    test_encryption_decryption(source_node, destination_node, "Encrypted message from Node 1!")
