from flask import Flask, request, jsonify
import os
import base64
import time
from utils.encryption_utils import EncryptionManager
from network.network_manager import NetworkManager
from network.route_manager import RouteManager
from network.packet import Packet
from utils.logging_utils import setup_logger

# Flask app for handling endpoints
app = Flask(__name__)
ground_station = None

class GroundStation:
    def __init__(self, node_id, position, port=6001):
        self.node_id = node_id  # Unique ID for the ground station
        self.position = position
        self.sequence_number = 0
        self.state = "ACTIVE"  # Possible states: ACTIVE, FAILED

        # Directory for received images (named after the ground station ID)
        self.received_images_dir = f"received_images_{self.node_id}"
        if not os.path.exists(self.received_images_dir):
            os.makedirs(self.received_images_dir)

        # Initialize encryption, network, and routing managers
        self.encryption_manager = EncryptionManager()
        self.network = NetworkManager(self)
        self.router = RouteManager(self)

        # Logger setup
        self.general_logger = setup_logger(self.node_id, "general")
        self.routing_logger = setup_logger(self.node_id, "routing")

        self.neighbor_public_keys = {}  # {node_id: public_key_bytes}
        self.shared_symmetric_keys = {}

        # Port for Flask server
        self.port = port

    def save_received_image(self, image_data, source_id):
        """
        Save a received image to disk.
        """
        image_path = os.path.join(self.received_images_dir, f"image_from_satellite_{source_id}_{int(time.time())}.png")
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)
        return image_path

    def is_active(self):       
        return self.state == "ACTIVE"

def initialize_station(station_id, position):
    """
    Initialize a ground station and set up its networking and encryption.

    Args:
        station_id (str): Unique identifier for the ground station.
        position (dict): Position of the station in the format {"x": float, "y": float, "z": float}.
    """
    global ground_station

    # Initialize the GroundStation instance
    ground_station = GroundStation(station_id, position)
    print(f"Ground station {station_id} initialized at position {position}")

    # Start network management services
    ground_station.network.start()

    # Broadcast the public key to neighbors
    ground_station.network.broadcast_public_key()

    # Log the initialization
    ground_station.general_logger.info(f"Ground station {station_id} setup complete with public key broadcasted.")



@app.route('/receive', methods=['POST'])
def receive_packet():
    """
    Handle incoming serialized packets and decrypt them.
    """
    serialized_packet = request.data

    try:
        # Deserialize the packet
        packet = Packet.from_bytes(serialized_packet)

        sender_id = packet.source_id
        if sender_id not in ground_station.shared_symmetric_keys:
            log(ground_station.general_logger, f"No symmetric key with Node {sender_id}. Cannot decrypt packet.", level="error")
            return jsonify({"error": "No symmetric key for decryption"}), 400

        # Decrypt the payload
        decrypted_payload = ground_station.encryption_manager.decrypt(packet.payload, ground_station.shared_symmetric_keys[sender_id])
        log(ground_station.general_logger, f"Successfully decrypted packet from Node {sender_id}: {decrypted_payload}")

        # Forward or process the packet
        if packet.dest_id == ground_station.node_id:
            log(ground_station.general_logger, f"Packet delivered to ground station: {decrypted_payload}")
            return jsonify({"status": "Packet delivered", "payload": decrypted_payload}), 200
        else:
            ground_station.router.forward_packet(packet)
            return jsonify({"status": "Packet forwarded"}), 200

    except Exception as e:
        log(ground_station.general_logger, f"Error processing packet: {str(e)}", level="error")
        return jsonify({"error": "Failed to process packet"}), 500


@app.route('/add_satellite', methods=['POST'])
def add_satellite():
    """
    Register a satellite node with the ground station.
    """
    data = request.get_json()
    node_id = data.get("node_id")
    node_address = data.get("node_address")

    if not node_id or not node_address:
        return jsonify({"error": "Node ID or Address missing"}), 400

    ground_station.network.neighbors[node_id] = node_address
    return jsonify({"status": "Satellite added"}), 200


@app.route('/update_position', methods=['POST'])
def update_position():
    """
    Update the position of a neighbor.
    """
    data = request.get_json()
    node_id = data.get("node_id")
    position = data.get("position")

    if not node_id or not position:
        return jsonify({"error": "Node ID or Position missing"}), 400

    ground_station.network.update_position_with_neighbor(node_id, position)
    return jsonify({"status": "Position updated"}), 200


@app.route('/receive_image_from_satellite', methods=['POST'])
def receive_image_from_satellite():
    """
    Decrypt and save an image from a satellite.
    """
    data = request.get_json()
    node_id = data.get("node_id")
    encrypted_image_data = data.get("image_data")  # Encrypted base64 image data

    if not node_id or not encrypted_image_data:
        return jsonify({"error": "Node ID or Image data missing"}), 400

    try:
        # Decode the base64 encrypted image
        encrypted_image_bytes = base64.b64decode(encrypted_image_data)

        # Decrypt the image
        decrypted_image = ground_station.encryption_manager.decrypt(encrypted_image_bytes)

        # Save the image
        image_path = ground_station.save_received_image(decrypted_image, node_id)

        return jsonify({"status": "Image received", "image_path": image_path}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to process the image: {str(e)}"}), 500

@app.route('/get_info', methods=['GET'])
def get_ground_station_info():
    """
    Get information about the ground station.
    """
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
