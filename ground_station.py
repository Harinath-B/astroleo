from flask import Flask, request, jsonify
import os
import requests
import time

class GroundStation:
    def __init__(self, port=6000):
        self.app = Flask(__name__)
        self.satellite_nodes = {}  # Placeholder for satellite nodes information
        self.received_images_dir = "ground_station_received_images"
        
        if not os.path.exists(self.received_images_dir):
            os.makedirs(self.received_images_dir)
        
        # Setting up routes
        self.app.add_url_rule('/add_satellite', 'add_satellite', self.add_satellite, methods=['POST'])
        self.app.add_url_rule('/get_satellites', 'get_satellites', self.get_satellites, methods=['GET'])
        self.app.add_url_rule('/send_message_to_satellite', 'send_message_to_satellite', self.send_message_to_satellite, methods=['POST'])
        self.app.add_url_rule('/receive_image_from_satellite', 'receive_image_from_satellite', self.receive_image_from_satellite, methods=['POST'])
        self.app.add_url_rule('/get_received_images', 'get_received_images', self.get_received_images, methods=['GET'])
        self.app.add_url_rule('/get_satellite_status', 'get_satellite_status', self.get_satellite_status, methods=['GET'])

        # Set the port for the Flask app
        self.port = port

    def save_received_image(self, image_data, source_id):
        """Simulate saving the received image from satellite."""
        image_path = os.path.join(self.received_images_dir, f"image_from_satellite_{source_id}_{int(time.time())}.png")
        with open(image_path, "wb") as img_file:
            img_file.write(image_data)
        return image_path

    def add_satellite_node(self, node_id, node_address):
        """Add a satellite node to the ground station's node list."""
        self.satellite_nodes[node_id] = node_address

    def add_satellite(self):
        """Endpoint to add a satellite node."""
        data = request.get_json()
        node_id = data.get("node_id")
        node_address = data.get("node_address")

        if not node_id or not node_address:
            return jsonify({"error": "Node ID or Address missing"}), 400

        self.add_satellite_node(node_id, node_address)
        return jsonify({"status": "satellite added", "node_id": node_id, "node_address": node_address}), 200

    def get_satellites(self):
        """Endpoint to list all satellite nodes."""
        return jsonify({"satellites": self.satellite_nodes}), 200

    def send_message_to_satellite(self):
        """Send a message to a satellite node."""
        data = request.get_json()
        node_id = data.get("node_id")
        message = data.get("message")

        if node_id not in self.satellite_nodes:
            return jsonify({"error": "Satellite node not found"}), 400

        satellite_address = self.satellite_nodes[node_id]
        payload = {"message": message}
        
        # Send a request to the satellite node (assuming it runs at 'node_address')
        try:
            response = requests.post(f"http://{satellite_address}/send", json=payload)
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

    def receive_image_from_satellite(self):
        """Receive an image from a satellite node."""
        data = request.get_json()
        node_id = data.get("node_id")
        image_data = data.get("image_data")

        if not node_id or not image_data:
            return jsonify({"error": "Node ID or Image data missing"}), 400

        # Save the received image
        image_path = self.save_received_image(image_data, node_id)
        return jsonify({"status": "image_received", "image_path": image_path}), 200

    def get_received_images(self):
        """List all received images stored by the ground station."""
        images = [os.path.join(self.received_images_dir, img) for img in os.listdir(self.received_images_dir) if img.endswith(".png")]
        return jsonify({"images": images}), 200

    def get_satellite_status(self):
        """Get status of all connected satellites."""
        status = {}
        for node_id, satellite_address in self.satellite_nodes.items():
            try:
                response = requests.get(f"http://{satellite_address}/get_satellite")
                status[node_id] = response.json()
            except requests.exceptions.RequestException:
                status[node_id] = {"status": "unreachable"}
        
        return jsonify({"status": status}), 200

    def run(self):
        """Run the Flask app."""
        self.app.run(host="0.0.0.0", port=self.port)

# Initialize and run the ground station
if __name__ == "__main__":
    ground_station = GroundStation(port=6000)
    ground_station.run()
