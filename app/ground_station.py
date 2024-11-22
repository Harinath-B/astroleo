# app/ground_station.py

from flask import Flask, request, jsonify
import os
import base64
import time
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import requests

from utils.logging_utils import setup_logger, log
from utils.encryption_utils import EncryptionManager
from network.network_manager import NetworkManager
from network.route_manager import RouteManager
from network.packet import Packet

session = requests.Session()
session.trust_env = False

app = Flask(__name__)
ground_station = None

class GroundStation:

    def __init__(self, node_id, position, port=6001):

        self.node_id = node_id  
        self.position = position
        self.sequence_number = 0
        self.state = "ACTIVE"  
       
        self.received_images_dir = f"ground_station_received_images/received_images_{self.node_id}"
        if not os.path.exists(self.received_images_dir):
            os.makedirs(self.received_images_dir)
        
        self.encryption_manager = EncryptionManager()
        self.network = NetworkManager(self)
        self.router = RouteManager(self)
        
        self.general_logger = setup_logger(self.node_id, "general")
        self.routing_logger = setup_logger(self.node_id, "routing")

        self.neighbor_public_keys = {}  
        self.shared_symmetric_keys = {}
        
        self.network.start()
        self.port = port

    def save_received_image(self, image_data, source_id):

        image_path = os.path.join(self.received_images_dir, f"image_from_satellite_{source_id}_{int(time.time())}.png")
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)
        return image_path

    def is_active(self):       
        return self.state == "ACTIVE"

def initialize_station(station_id, position):

    global ground_station   
    ground_station = GroundStation(1000 + station_id, position)
    print(f"Ground station {station_id} initialized at position {position}")   
    ground_station.network.broadcast_public_key()    
    ground_station.general_logger.info(f"Ground station {station_id} setup complete with public key broadcasted.")

@app.route('/broadcast_key', methods=['POST'])
def broadcast_key():
   
    if not ground_station or not ground_station.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    neighbor_id = data.get("neighbor_id")
    if not neighbor_id:
        return jsonify({"error": "Neighbor ID not provided"}), 400

    neighbor_address = ground_station.network.get_neighbor_address(neighbor_id)
    if not neighbor_address:
        return jsonify({"error": f"Neighbor {neighbor_id} not found"}), 404

    public_key = ground_station.encryption_manager.get_public_key()
    response = session.post(
        f"{neighbor_address}/exchange_key",
        json={"node_id": ground_station.node_id, "public_key": public_key},
    )

    if response.status_code == 200:
        return jsonify({"status": "broadcast_successful"}), 200
    return jsonify({"status": "broadcast_failed", "error": response.json()}), response.status_code


@app.route('/receive', methods=['POST'])
def receive_packet():

    data = request.get_data()
    try:        
        packet = Packet.from_bytes(data)
        sender_id = packet.source_id
        if sender_id not in ground_station.shared_symmetric_keys:
            log(ground_station.general_logger, f"No symmetric key with Node {sender_id}. Cannot decrypt packet.", level="error")
            return jsonify({"error": "No symmetric key for decryption"}), 400
        
        decrypted_payload = ground_station.encryption_manager.decrypt(packet.payload, ground_station.shared_symmetric_keys[sender_id])
        log(ground_station.general_logger, f"Successfully decrypted packet from Node {sender_id}: {decrypted_payload}")
        
        if packet.dest_id == ground_station.node_id:
            log(ground_station.general_logger, f"Packet delivered to ground station: {decrypted_payload}")
            return jsonify({"status": "Packet delivered", "payload": decrypted_payload.decode()}), 200
        ground_station.router.forward_packet(packet)
        return jsonify({"status": "Packet forwarded"}), 200

    except Exception as e:
        log(ground_station.general_logger, f"Error processing packet: {str(e)}", level="error")
        return jsonify({"error": "Failed to process packet"}), 500

@app.route('/receive_routing_table', methods=['POST'])
def receive_routing_table():
   
    if not ground_station or not ground_station.is_active():
        return jsonify({"error": "Node is offline"}), 400
    received_table = request.get_json()
    sender_id = int(request.remote_addr.split('.')[-1])  
    ground_station.network.update_routing_table(received_table, sender_id)
    return jsonify({"status": "received"}), 200

@app.route('/add_satellite', methods=['POST'])
def add_satellite():

    data = request.get_json()
    node_id = data.get("node_id")
    node_address = data.get("node_address")
    if not node_id or not node_address:
        return jsonify({"error": "Node ID or Address missing"}), 400

    ground_station.network.neighbors[node_id] = node_address
    return jsonify({"status": "Satellite added"}), 200

@app.route('/exchange_key', methods=['POST'])
def exchange_key():
   
    if not ground_station or not ground_station.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    sender_id = data.get("node_id")
    public_key_base64 = data.get("public_key")
    if not sender_id or not public_key_base64:
        return jsonify({"error": "Invalid data provided"}), 400

    try:        
        public_key_pem = base64.b64decode(public_key_base64)
        public_key = load_pem_public_key(public_key_pem)

        ground_station.neighbor_public_keys[sender_id] = public_key
        shared_key = ground_station.encryption_manager.generate_shared_secret(public_key_pem)
        ground_station.shared_symmetric_keys[sender_id] = shared_key
        log(ground_station.general_logger, f"[[KEY] {ground_station.shared_symmetric_keys}")

        log(ground_station.general_logger, f"Key exchange successful with Node {sender_id}")
        return jsonify({"status": "key_exchange_successful"}), 200

    except Exception as e:
        log(ground_station.general_logger, f"Error during key exchange with Node {sender_id}: {str(e), public_key_base64}", level="error")
        return jsonify({"error": "Key exchange failed"}), 500

@app.route('/update_position', methods=['POST'])
def update_position():

    data = request.get_json()
    node_id = data.get("node_id")
    position = data.get("position")
    if not node_id or not position:
        return jsonify({"error": "Node ID or Position missing"}), 400

    ground_station.network.update_position_with_neighbor(node_id, position)
    return jsonify({"status": "Position updated"}), 200

@app.route('/receive_image_from_satellite', methods=['POST'])
def receive_image_from_satellite():

    data = request.get_data()
    try:        
        ground_station.router.receive_packet(data)
        return jsonify({"status": "Image received and being processed"}), 200

    except Exception as e:
        log(ground_station.general_logger, f"Error in /receive_image_from_satellite: {str(e)}", level="error")
        return jsonify({"error": f"Failed to process the image: {str(e)}"}), 500

@app.route('/get_received_images', methods=['GET'])
def get_received_images():

    if not ground_station or not ground_station.is_active():
        return jsonify({"error": "Node is offline"}), 400

    try:        
        images = [
            os.path.join(ground_station.received_images_dir, img)
            for img in os.listdir(ground_station.received_images_dir)
            if img.endswith((".png", ".jpg", ".jpeg"))
        ]
        return jsonify({"status": "success", "images": images}), 200

    except Exception as e:
        log(ground_station.general_logger, f"Error retrieving received images: {str(e)}", level="error")
        return jsonify({"error": f"Failed to retrieve received images: {str(e)}"}), 500


@app.route('/get_info', methods=['GET'])
def get_ground_station_info():

    try:
        info = {
            "node_id": ground_station.node_id,
            "position": ground_station.position,
            "state": ground_station.state,
            "received_images_dir": ground_station.received_images_dir,
            "neighbor_count": len(ground_station.network.neighbors),
            "shared_keys_count": len(ground_station.shared_symmetric_keys)
        }
        return jsonify({"status": "success", "ground_station_info": info}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve ground station info: {str(e)}"}), 500
