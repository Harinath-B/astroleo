from flask import Flask, request, jsonify
from network.network_manager import NetworkManager
from network.route_manager import RouteManager
from network.packet import Packet
from utils.logging_utils import setup_logger, log
from utils.encryption_utils import EncryptionManager
import struct
import os
import time
from PIL import Image
import zlib

app = Flask(__name__)
satellite = None  # Global instance for the satellite node

class SatelliteNode:
    def __init__(self, node_id, position):
        self.node_id = node_id
        self.position = position
        self.sequence_number = 0

        # Initialize Encryption Manager with a unique key
        self.encryption_manager = EncryptionManager(b"sixteenbytekey!!")

        # Initialize Network and Route Managers
        self.network = NetworkManager(self)
        self.router = RouteManager(self)

        # Initialize loggers for general and routing actions
        self.general_logger = setup_logger(self.node_id, "general")
        self.routing_logger = setup_logger(self.node_id, "routing")

        # Start discovery process to find neighbors
        self.network.start_discovery()

    def create_packet(self, dest_id, payload, message_type=1):
        """Create a packet with specified destination, payload, and message type."""
        packet = Packet(
            version=1,
            message_type=message_type,
            source_id=self.node_id,
            dest_id=dest_id,
            sequence_number=self.sequence_number,
            payload=payload,
            ttl=10,
            encryption_manager=self.encryption_manager
        )
        self.sequence_number += 1
        return packet

    def receive_packet(self, data):
        """Handle an incoming packet."""
        log(self.general_logger, f"Raw data received: {data}")

        try:
            packet = Packet.from_bytes(data, encryption_manager=self.encryption_manager)
        except struct.error as e:
            log(self.general_logger, f"Failed to unpack packet: {e}")
            return {"status": "error", "message": "Invalid packet format"}
        
        decrypted_payload = packet.get_payload()
        self.last_received_packet = {"source_id": packet.source_id, "decrypted_payload": decrypted_payload}
        log(self.general_logger, f"Received packet (Type: {packet.message_type}) from Node {packet.source_id} with payload: {decrypted_payload}")
        
        if packet.message_type == 2:  # Image packet
            try:
                decrypted_payload = zlib.decompress(decrypted_payload)
            except zlib.error as e:
                log(self.general_logger, f"Failed to decompress image data: {e}")
                return {"status": "error", "message": "Decompression failed"}
            image_path = f"received_images/image_from_node_{packet.source_id}.png"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as img_file:
                img_file.write(decrypted_payload)
            log(self.general_logger, f"Image saved to {image_path}")
            return {"status": "image_received", "image_path": image_path}

        if packet.message_type == 2:  # Handle image packets
            image_path = f"received_images/image_from_node_{packet.source_id}.png"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as img_file:
                img_file.write(decrypted_payload)
            log(self.general_logger, f"Image saved to {image_path}")
            return {"status": "image_received", "image_path": image_path}

        # Check if this is the destination
        if packet.dest_id == self.node_id:
            log(self.general_logger, f"Packet successfully delivered to Node {self.node_id}")
            return {"status": "success", "data": decrypted_payload}

        # Otherwise, forward the packet
        log(self.general_logger, f"Node {self.node_id}: Forwarding packet to destination {packet.dest_id}")
        self.router.forward_packet(packet)
        return {"status": "processed"}

    def transmit_image(self, dest_id, image_path):
        """Transmit an image to a destination node."""
        try:
            with open(image_path, "rb") as img_file:
                image_data = img_file.read()
        except FileNotFoundError:
            log(self.general_logger, f"Image file not found: {image_path}")
            return False

        image_data = zlib.compress(image_data)
        packet = self.create_packet(dest_id=dest_id, payload=image_data, message_type=2)
        success = self.router.forward_packet(packet)
        return success

    def to_json(self):
        """Serialize the SatelliteNode instance to JSON."""
        return {
            "node_id": self.node_id,
            "position": self.position,
            "sequence_number": self.sequence_number,
            "routing_table": self.network.routing_table,
            "neighbors": self.network.neighbors
        }

def capture_image(image_dir="images"):
    """Capture or simulate an image."""
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    image_name = f"astro_image_{int(time.time())}.png"
    image_path = os.path.join(image_dir, image_name)

    # Simulate a dummy image (replace with actual camera functionality)
    img = Image.new('RGB', (1024, 1024), color=(0, 0, 255))
    img.save(image_path)
    return image_path

def initialize_node(node_id, position):
    """Initialize the satellite node with a unique ID and position."""
    global satellite
    satellite = SatelliteNode(node_id, position)
    print(f"Satellite node {node_id} initialized at position {position}")
    satellite.network.start_heartbeat()

@app.route('/capture_image', methods=['POST'])
def capture_image_endpoint():
    """Capture an image and return its path."""
    image_path = capture_image()
    return jsonify({"status": "success", "image_path": image_path}), 200

@app.route('/transmit_image', methods=['POST'])
def transmit_image():
    """Transmit an image to a destination node."""
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
    """List all received images."""
    image_dir = "received_images"
    if not os.path.exists(image_dir):
        return jsonify({"images": []}), 200

    images = [os.path.join(image_dir, img) for img in os.listdir(image_dir) if img.endswith(".png")]
    return jsonify({"images": images}), 200

@app.route('/send', methods=['POST'])
def send_message():
    """Endpoint to send a message to a destination node."""
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
    """Endpoint to handle incoming packets."""
    data = request.get_data()
    log(satellite.general_logger, f"Raw data received: {data}")  # Log received data
    if not data:
        return jsonify({"status": "error", "message": "Empty data received"}), 400

    response = satellite.receive_packet(data)
    return jsonify(response), 200


@app.route('/update_position', methods=['POST'])
def update_position():
    """Endpoint to receive position updates from other nodes."""
    data = request.get_json()
    neighbor_id = data['node_id']
    position = tuple(data['position'])
    satellite.network.update_position(neighbor_id, position)
    return jsonify({"status": "position updated"}), 200

@app.route('/receive_routing_table', methods=['POST'])
def receive_routing_table():
    """Endpoint to receive and update the routing table from a neighbor."""
    received_table = request.get_json()
    sender_id = int(request.remote_addr.split('.')[-1])  # Simplified sender ID detection
    satellite.network.update_routing_table(received_table, sender_id)
    return jsonify({"status": "received"}), 200

@app.route('/get_routing_table', methods=['GET'])
def get_routing_table():
    """Endpoint to retrieve the current routing table for a node."""
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
    """Endpoint to return the serialized SatelliteNode instance."""
    return jsonify(satellite.to_json()), 200

@app.route('/get_last_received_packet', methods=['GET'])
def get_last_received_packet():
    """Endpoint to retrieve the last received packet."""
    if satellite.last_received_packet:
        return jsonify(satellite.last_received_packet), 200
    return jsonify({"error": "No packet received yet"}), 404

@app.route('/heartbeat', methods=['POST'])
def handle_heartbeat():
    """Endpoint to handle incoming heartbeat packets."""
    data = request.get_json()
    sender_id = data.get("node_id")
    timestamp = data.get("timestamp")

    if not sender_id or not timestamp:
        return jsonify({"status": "error", "message": "Invalid heartbeat data"}), 400

    satellite.network.receive_heartbeat(sender_id, timestamp)
    return jsonify({"status": "success"}), 200

@app.route('/get_neighbors', methods=['GET'])
def get_neighbors():
    """
    Retrieve the list of active neighbors and their details.
    :return: JSON object with neighbors and their attributes.
    """
    neighbors = satellite.network.neighbors
    response = {
        neighbor_id: {
            "position": position_distance[0],
            "distance": position_distance[1]
        }
        for neighbor_id, position_distance in neighbors.items()
    }
    return jsonify(response), 200



if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python satellite_node.py <node_id> <x> <y> <z>")
        sys.exit(1)

    node_id = int(sys.argv[1])
    position = (float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]))
    initialize_node(node_id, position)
    app.run(host="0.0.0.0", port=5000 + node_id)
