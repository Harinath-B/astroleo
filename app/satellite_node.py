from network.network_manager import NetworkManager
from network.route_manager import RouteManager
from network.packet import Packet
from utils.logging_utils import setup_logger, log
from utils.encryption_utils import *
from utils.image_utils import *
import zlib
import requests

satellite = None  # Global instance for the satellite node

class SatelliteNode:
    def __init__(self, node_id, position):
        self.node_id = node_id
        self.position = position
        self.sequence_number = 0
        
        self.last_received_packet = None

        # Initialize Encryption Manager with a unique key
        self.encryption_manager = EncryptionManager()

        # Initialize Network and Route Managers
        self.network = NetworkManager(self)
        self.router = RouteManager(self)

        # Initialize loggers for general and routing actions
        self.general_logger = setup_logger(self.node_id, "general")
        self.routing_logger = setup_logger(self.node_id, "routing")
        
        self.neighbor_public_keys = {}  # {node_id: public_key_bytes}
        self.shared_symmetric_keys = {}

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
            ttl=10
        )
        self.sequence_number += 1
        return packet

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
    
    def exchange_keys_with_neighbor(self, neighbor_id):
        """
        Exchange public keys with a specific neighbor and establish a shared symmetric key.
        """
        try:
            neighbor_address = self.network.get_neighbor_address(neighbor_id)
            if not neighbor_address:
                log(self.general_logger, f"Neighbor {neighbor_id} address not found", level="error")
                return False

            # Send this node's public key to the neighbor
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
        """
        Establish a shared symmetric key with a neighbor using their public key.
        """
        shared_key = self.encryption_manager.generate_shared_secret(public_key_bytes)
        self.shared_symmetric_keys[neighbor_id] = shared_key
        log(self.general_logger, f"Node {self.node_id}: Established symmetric key with Node {neighbor_id}")


    def to_json(self):
        """Serialize the SatelliteNode instance to JSON."""
        return {
            "node_id": self.node_id,
            "position": self.position,
            "sequence_number": self.sequence_number,
            "routing_table": self.network.routing_table,
            "neighbors": self.network.neighbors
        }



def initialize_node(node_id, position):
    """
    Initialize the satellite node with a unique ID and position.
    """
    global satellite
    satellite = SatelliteNode(node_id, position)
    print(f"Satellite node {node_id} initialized at position {position}")
    satellite.network.start_heartbeat()
    satellite.network.broadcast_public_key()
