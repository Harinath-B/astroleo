# app/satellite_node.py

from network.network_manager import NetworkManager
from network.route_manager import RouteManager
from network.sync_manager import SyncManager
from network.packet import Packet
from utils.logging_utils import setup_logger, log
from utils.encryption_utils import *
from utils.image_utils import *
import zlib
import requests
from flask import Blueprint, request, jsonify, Flask
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64

app = Flask(__name__)
satellite = None  # Global instance for the satellite node


class SatelliteNode:
    def __init__(self, node_id, position):
        self.node_id = node_id
        self.position = position
        self.sequence_number = 0
        self.state = "ACTIVE"  # Possible states: ACTIVE, FAILED

        self.last_received_packet = None

        # Initialize Encryption Manager with a unique key
        self.encryption_manager = EncryptionManager()

        # Initialize Network and Route Managers
        self.network = NetworkManager(self)
        self.router = RouteManager(self)
        
        self.sync_manager = SyncManager(self.node_id, self.network.get_neighbor_addresses)

        # Initialize loggers for general and routing actions
        self.general_logger = setup_logger(self.node_id, "general")
        self.routing_logger = setup_logger(self.node_id, "routing")

        self.neighbor_public_keys = {}  # {node_id: public_key_bytes}
        self.shared_symmetric_keys = {}

        # Start discovery process to find neighbors
        self.network.start()
        self.sync_manager.start()
        
        
    def get_local_time(self):
       
        return self.sync_manager.get_local_time()
    
    def synchronize_time(self, neighbor_times):

        self.sync_manager.synchronize(neighbor_times)

    def share_local_time(self):
       
        return {self.node_id: self.get_local_time()}

    def is_active(self):
       
        return self.state == "ACTIVE"

    def fail(self):
       
        self.state = "FAILED"
        log(self.general_logger, f"Node {self.node_id} has FAILED and is offline.")

    def recover(self):
       
        self.state = "ACTIVE"
        log(self.general_logger, f"Node {self.node_id} has RECOVERED and is back online.")

    def create_packet(self, dest_id, payload, message_type=1):
       
        if not self.is_active():
            log(self.general_logger, "Node is offline and cannot create a packet.")
            return None

        packet = Packet(
            version=1,
            message_type=message_type,
            source_id=self.node_id,
            dest_id=dest_id,
            sequence_number=self.sequence_number,
            payload=payload,
            ttl=10
        )
        self.sequence_number += 1
        return packet

    def transmit_image(self, dest_id, image_path):
       
        if not self.is_active():
            log(self.general_logger, "Node is offline and cannot transmit an image.")
            return False

        try:
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
        except FileNotFoundError:
            log(self.general_logger, f"Image file not found: {image_path}")
            return False

        image_data = zlib.compress(image_data)
        packet = self.create_packet(dest_id=dest_id, payload=image_data, message_type=2)
        if not packet:
            return False

        success = self.router.forward_packet(packet)
        return success

    def exchange_keys_with_neighbor(self, neighbor_id):
       

        if not self.is_active():
            log(self.general_logger, "Node is offline and cannot exchange keys.")
            return False

        try:
            neighbor_address = self.network.get_neighbor_address(neighbor_id)
            if not neighbor_address:
                log(self.general_logger, f"Neighbor {neighbor_id} address not found", level="error")
                return False

            public_key = self.encryption_manager.get_public_key()
            response = requests.post(
                f"{neighbor_address}/exchange_key",
                json={"node_id": self.node_id, "public_key": public_key},
            )

            if response.status_code == 200:
                log(self.general_logger, f"Key exchange with Node {neighbor_id} successful")
                return True
            else:
                log(self.general_logger, f"Key exchange with Node {neighbor_id} failed: {response.status_code}", level="error")
                return False
        except Exception as e:
            log(self.general_logger, f"Error during key exchange with Node {neighbor_id}: {e}", level="error")
            return False

    def establish_symmetric_key(self, neighbor_id, public_key_bytes):
       
       
        shared_key = self.encryption_manager.generate_shared_secret(public_key_bytes)
        self.shared_symmetric_keys[neighbor_id] = shared_key
        log(self.general_logger, f"Node {self.node_id}: Established symmetric key with Node {neighbor_id}")

    def to_json(self):
       
        return {
            "node_id": self.node_id,
            "position": self.position,
            "sequence_number": self.sequence_number,
            "routing_table": self.network.routing_table,
            "neighbors": self.network.neighbors
        }


def initialize_node(node_id, position):
   
   
    global satellite
    satellite = SatelliteNode(node_id, position)
    print(f"Satellite node {node_id} initialized at position {position}")

    satellite.network.broadcast_public_key()

@app.route('/fail', methods=['POST'])
def fail_node():
   
    if satellite:
        satellite.fail()
        return jsonify({"status": "Node has FAILED"}), 200
    return jsonify({"error": "Satellite instance not initialized"}), 400


@app.route('/recover', methods=['POST'])
def recover_node():
   
    if satellite:
        satellite.recover()
        return jsonify({"status": "Node has RECOVERED"}), 200
    return jsonify({"error": "Satellite instance not initialized"}), 400


@app.route('/capture_image', methods=['POST'])
def capture_image_endpoint():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    image_path = capture_image()
    return jsonify({"status": "success", "image_path": image_path}), 200


@app.route('/transmit_image', methods=['POST'])
def transmit_image():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    dest_id = data.get("dest_id")
    image_path = data.get("image_path")

    if not dest_id or not image_path:
        return jsonify({"error": "Destination ID or image path not provided"}), 400

    success = satellite.transmit_image(dest_id=dest_id, image_path=image_path)

    if success:
        return jsonify({"status": "image_transmitted"}), 200
    else:
        return jsonify({"status": "transmission_failed"}), 400


@app.route('/get_received_images', methods=['GET'])
def get_received_images():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    image_dir = "received_images"
    if not os.path.exists(image_dir):
        return jsonify({"images": []}), 200

    images = [os.path.join(image_dir, img) for img in os.listdir(image_dir) if img.endswith(".png")]
    return jsonify({"images": images}), 200


@app.route('/send', methods=['POST'])
def send_message():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    dest_id = data.get("dest_id")
    payload = data.get("payload", "")
    if not dest_id:
        return jsonify({"error": "Destination ID not provided"}), 400

    packet = satellite.create_packet(dest_id=dest_id, payload=payload, message_type=1)
    success = satellite.router.forward_packet(packet)

    if success:
        return jsonify({"status": "packet_sent"}), 200
    else:
        return jsonify({"status": "packet_failed"}), 400


@app.route('/receive', methods=['POST'])
def receive():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_data()
    log(satellite.general_logger, f"Raw data received: {data}")  # Log received data
    if not data:
        return jsonify({"status": "error", "message": "Empty data received"}), 400

    response = satellite.router.receive_packet(data)
    log(satellite.routing_logger, f"last received packet: {satellite.last_received_packet}")
    return jsonify(response), 200


@app.route('/get_position', methods=['GET'])
def get_position():
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    return jsonify(satellite.position)


@app.route('/get_keys', methods=['GET'])
def get_keys():
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    return jsonify({f"{satellite.node_id}": {"Shared": str(satellite.shared_symmetric_keys), "Public": str(satellite.neighbor_public_keys)}})


@app.route('/update_position', methods=['POST'])
def update_position():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    neighbor_id = data['node_id']
    position = tuple(data['position'])
    satellite.network.update_position_with_neighbor(neighbor_id, position)
    return jsonify({"status": "position updated"}), 200


@app.route('/receive_routing_table', methods=['POST'])
def receive_routing_table():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    received_table = request.get_json()
    sender_id = int(request.remote_addr.split('.')[-1])  # Simplified sender ID detection
    satellite.network.update_routing_table(received_table, sender_id)
    return jsonify({"status": "received"}), 200


@app.route('/get_routing_table', methods=['GET'])
def get_routing_table():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    try:
        routing_table = satellite.network.routing_table
        # Convert routing table to JSON-serializable format
        serializable_routing_table = {
            str(k): list(v) if isinstance(v, tuple) else v
            for k, v in routing_table.items()
        }
        log(satellite.general_logger, f"Serialized routing table for Node {satellite.node_id}: {serializable_routing_table}")
        return jsonify(serializable_routing_table), 200
    except Exception as e:
        log(satellite.general_logger, f"Error in /get_routing_table for Node {satellite.node_id}: {e}", level="error")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/get_satellite', methods=['GET'])
def get_satellite():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    return jsonify(satellite.to_json()), 200


@app.route('/heartbeat', methods=['POST'])
def handle_heartbeat():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    sender_id = data.get("node_id")
    timestamp = data.get("timestamp")

    if not sender_id or not timestamp:
        return jsonify({"status": "error", "message": "Invalid heartbeat data"}), 400

    satellite.network.receive_heartbeat(sender_id, timestamp)
    return jsonify({"status": "success"}), 200


@app.route('/get_neighbors', methods=['GET'])
def get_neighbors():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    neighbors = satellite.network.neighbors
    response = {
        neighbor_id: {
            "position": position_distance[0],
            "distance": position_distance[1]
        }
        for neighbor_id, position_distance in neighbors.items()
    }
    return jsonify(response), 200


@app.route('/broadcast_key', methods=['POST'])
def broadcast_key():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    neighbor_id = data.get("neighbor_id")
    if not neighbor_id:
        return jsonify({"error": "Neighbor ID not provided"}), 400

    neighbor_address = satellite.network.get_neighbor_address(neighbor_id)
    if not neighbor_address:
        return jsonify({"error": f"Neighbor {neighbor_id} not found"}), 404

    public_key = satellite.encryption_manager.get_public_key()
    response = requests.post(
        f"{neighbor_address}/exchange_key",
        json={"node_id": satellite.node_id, "public_key": public_key},
    )

    if response.status_code == 200:
        return jsonify({"status": "broadcast_successful"}), 200
    else:
        return jsonify({"status": "broadcast_failed", "error": response.json()}), response.status_code


@app.route('/exchange_key', methods=['POST'])
def exchange_key():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    sender_id = data.get("node_id")
    public_key_base64 = data.get("public_key")
    if not sender_id or not public_key_base64:
        return jsonify({"error": "Invalid data provided"}), 400

    try:
        # Decode and deserialize the public key
        public_key_pem = base64.b64decode(public_key_base64)
        public_key = load_pem_public_key(public_key_pem)

        # Store sender's public key and derive a shared symmetric key
        satellite.neighbor_public_keys[sender_id] = public_key
        shared_key = satellite.encryption_manager.generate_shared_secret(public_key_pem)

        satellite.shared_symmetric_keys[sender_id] = shared_key
        log(satellite.general_logger, f"[[KEY] {satellite.shared_symmetric_keys}")

        log(satellite.general_logger, f"Key exchange successful with Node {sender_id}")
        return jsonify({"status": "key_exchange_successful"}), 200
    except Exception as e:
        log(satellite.general_logger, f"Error during key exchange with Node {sender_id}: {str(e), public_key_base64}", level="error")
        return jsonify({"error": "Key exchange failed"}), 500
    
@app.route('/get_local_time', methods=['GET'])
def get_local_time():
   
    if not satellite:
        return jsonify({"error": "Satellite instance not initialized"}), 400
    return jsonify({"local_time": satellite.sync_manager.get_local_time()}), 200

@app.route('/synchronize_time', methods=['POST'])
def synchronize_time():
   
    if not satellite or not satellite.is_active():
        return jsonify({"error": "Node is offline"}), 400

    data = request.get_json()
    neighbor_times = data.get("neighbor_times")

    if not neighbor_times:
        return jsonify({"error": "Neighbor times not provided"}), 400

    satellite.synchronize_time(neighbor_times)
    return jsonify({"status": "synchronized", "local_time": satellite.get_local_time()}), 200

