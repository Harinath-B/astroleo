import requests

BASE_PORT = 5000

def test_communication(sender_id, receiver_id, message):
    """
    Test communication by sending a message from one node to another and verifying the received message.
    """
    send_url = f"http://127.0.0.1:{BASE_PORT + sender_id}/send"

    # Send the message
    data = {"dest_id": receiver_id, "payload": message}
    try:
        send_response = requests.post(send_url, json=data)
        if send_response.status_code != 200:
            print(f"Message from Node {sender_id} to Node {receiver_id} failed: {send_response.json()}")
            return False
        print(f"Message from Node {sender_id} to Node {receiver_id} sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending message from Node {sender_id} to Node {receiver_id}: {e}")
        return False

    # Allow some time for the message to be processed
    import time
    time.sleep(1)

def main():
    # Define the node IDs
    node_ids = [1, 2, 3, 4, 5]  # Adjust based on the running nodes

    # Test communication between all nodes
    message = "Hello from Node"
    for sender_id in node_ids:
        for receiver_id in node_ids:
            if sender_id != receiver_id:  # Avoid sending to itself
                test_communication(sender_id, receiver_id, f"{message} {sender_id}")

if __name__ == "__main__":
    main()
