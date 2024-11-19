from flask import Blueprint, request, jsonify
from app.satellite_node import satellite
from satellite_node import *
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64

routes = Blueprint("routes", __name__)

@routes.route('/capture_image', methods=['POST'])
def capture_image_endpoint():
    """Capture an image and return its path."""
    image_path = capture_image()
    return jsonify({"status": "success", "image_path": image_path}), 200

@routes.route('/transmit_image', methods=['POST'])
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

@routes.route('/get_received_images', methods=['GET'])
def get_received_images():
    """List all received images."""
    image_dir = "received_images"
    if not os.path.exists(image_dir):
        return jsonify({"images": []}), 200

    images = [os.path.join(image_dir, img) for img in os.listdir(image_dir) if img.endswith(".png")]
    return jsonify({"images": images}), 200

@routes.route('/send', methods=['POST'])
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
    
@routes.route('/receive', methods=['POST'])
def receive():
    """Endpoint to handle incoming packets."""
    data = request.get_data()
    log(satellite.general_logger, f"Raw data received: {data}")  # Log received data
    if not data:
        return jsonify({"status": "error", "message": "Empty data received"}), 400

    
    response = satellite.router.receive_packet(data)
    return jsonify(response), 200


@routes.route('/update_position', methods=['POST'])
def update_position():
    """Endpoint to receive position updates from other nodes."""
    data = request.get_json()
    neighbor_id = data['node_id']
    position = tuple(data['position'])
    satellite.network.update_position(neighbor_id, position)
    return jsonify({"status": "position updated"}), 200

@routes.route('/receive_routing_table', methods=['POST'])
def receive_routing_table():
    """Endpoint to receive and update the routing table from a neighbor."""
    received_table = request.get_json()
    sender_id = int(request.remote_addr.split('.')[-1])  # Simplified sender ID detection
    satellite.network.update_routing_table(received_table, sender_id)
    return jsonify({"status": "received"}), 200

@routes.route('/get_routing_table', methods=['GET'])
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

@routes.route('/get_satellite', methods=['GET'])
def get_satellite():
    """Endpoint to return the serialized SatelliteNode instance."""
    return jsonify(satellite.to_json()), 200

@routes.route('/get_last_received_packet', methods=['GET'])
def get_last_received_packet():
    """Endpoint to retrieve the last received packet."""
    if satellite.last_received_packet:
        return jsonify(satellite.last_received_packet.payload), 200
    return jsonify({"error": "No packet received yet"}), 404

@routes.route('/heartbeat', methods=['POST'])
def handle_heartbeat():
    """Endpoint to handle incoming heartbeat packets."""
    data = request.get_json()
    sender_id = data.get("node_id")
    timestamp = data.get("timestamp")

    if not sender_id or not timestamp:
        return jsonify({"status": "error", "message": "Invalid heartbeat data"}), 400

    satellite.network.receive_heartbeat(sender_id, timestamp)
    return jsonify({"status": "success"}), 200

@routes.route('/get_neighbors', methods=['GET'])
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


@routes.route('/broadcast_key', methods=['POST'])
def broadcast_key():
    """
    Endpoint to send this node's public key to a specific neighbor node.
    """
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

@routes.route('/exchange_key', methods=['POST'])
def exchange_key():
    """
    Endpoint to receive a public key from another node and derive a shared symmetric key.
    """
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
        log(satellite.general_logger,f"[[KEY] {satellite.shared_symmetric_keys}")

        log(satellite.general_logger, f"Key exchange successful with Node {sender_id}")
        return jsonify({"status": "key_exchange_successful"}), 200
    except Exception as e:
        log(satellite.general_logger, f"Error during key exchange with Node {sender_id}: {str(e), public_key_base64}", level="error")
        return jsonify({"error": "Key exchange failed"}), 500

