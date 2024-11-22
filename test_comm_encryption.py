import requests
import time

from app.config import BASE_PORT

session = requests.Session()
session.trust_env = False

def test_communication(sender_id, receiver_id, message):
    
    send_url = f"http://10.35.70.23:{BASE_PORT + sender_id}/send"
    data = {"dest_id": receiver_id, "payload": message}
    try:
        send_response = session.post(send_url, json=data)
        if send_response.status_code != 200:
            print(f"Message from Node {sender_id} to Node {receiver_id} failed: {send_response.json()}")
            return False
        print(f"Message from Node {sender_id} to Node {receiver_id} sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending message from Node {sender_id} to Node {receiver_id}: {e}")
        return False    
    time.sleep(1)

def main():
    
    node_ids = [1, 2, 3, 4, 5]      
    message = "Hello from Node"
    for sender_id in node_ids:
        for receiver_id in node_ids:
            if sender_id != receiver_id:  
                test_communication(sender_id, receiver_id, f"{message} {sender_id}")

if __name__ == "__main__":
    main()
