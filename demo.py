import os
import time
import subprocess
from threading import Thread
from requests import Session
from utils.logging_utils import setup_logger, log
import networkx as nx
import matplotlib.pyplot as plt

# Initialize logger
DEMO_LOG = setup_logger("demo", "log")

# Constants
NUM_SATELLITES = 5
NUM_GROUND_STATIONS = 2
BASE_IP = "10.35.70.23"
BASE_PORT = 5000
RESULTS_DIR = "demo_results"

# Session for HTTP requests
session = Session()
session.trust_env = False

def prepare_directories():
    """Prepare results and log directories."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(os.path.join(RESULTS_DIR, "images"), exist_ok=True)
    os.makedirs("logs", exist_ok=True)

def launch_nodes():
    """Launch satellite nodes."""
    log(DEMO_LOG, "Launching satellite nodes...")
    Thread(target=lambda: subprocess.run(
        ["python3", "launch_nodes.py", str(NUM_SATELLITES)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )).start()
    time.sleep(2)

def launch_stations():
    """Launch ground stations."""
    log(DEMO_LOG, "Launching ground stations...")
    Thread(target=lambda: subprocess.run(
        ["python3", "launch_stations.py", str(NUM_GROUND_STATIONS)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )).start()
    time.sleep(2)

def initialize_demo():
    """Initialize satellites and ground stations."""
    log(DEMO_LOG, "Initializing satellite nodes and ground stations...")
    launch_nodes()
    launch_stations()
    time.sleep(10)
    log(DEMO_LOG, "Initialization complete.")

def key_exchange():
    """Perform key exchange between satellites and ground stations."""
    log(DEMO_LOG, "Starting key exchange...")
    for sat_id in range(1, NUM_SATELLITES + 1):
        for gs_id in range(1001, 1001 + NUM_GROUND_STATIONS):
            gs_port = BASE_PORT + gs_id
            sat_port = BASE_PORT + sat_id
            try:
                session.post(f"http://{BASE_IP}:{sat_port}/broadcast_key")
                session.post(f"http://{BASE_IP}:{gs_port}/broadcast_key")
                log(DEMO_LOG, f"Key exchange between Satellite {sat_id} and Ground Station {2001 + gs_id} complete.")
            except Exception as e:
                log(DEMO_LOG, f"Key exchange failed for Satellite {sat_id} and Ground Station {2001 + gs_id}: {e}")

def capture_and_transmit_images():
    """Capture and transmit images from satellites."""
    log(DEMO_LOG, "Capturing and transmitting images from satellites...")
    for sat_id in range(1, NUM_SATELLITES + 1):
        port = BASE_PORT + sat_id
        capture_url = f"http://{BASE_IP}:{port}/capture_image"
        try:
            response = session.post(capture_url)
            if response.status_code == 200:
                log(DEMO_LOG, f"Satellite {sat_id}: Image captured and transmitted successfully.")
            else:
                log(DEMO_LOG, f"Satellite {sat_id}: Failed to capture and transmit image: {response.text}")
        except Exception as e:
            log(DEMO_LOG, f"Satellite {sat_id}: Error during image capture: {e}")

def list_received_images():
    """Retrieve and validate received images at ground stations."""
    log(DEMO_LOG, "Listing received images from ground stations...")
    for gs_id in range(NUM_GROUND_STATIONS):
        port = BASE_PORT + 2001 + gs_id
        url = f"http://{BASE_IP}:{port}/get_received_images"
        try:
            response = session.get(url)
            if response.status_code == 200:
                images = response.json()["images"]
                log(DEMO_LOG, f"Ground Station {2001 + gs_id}: Received images: {images}")
                save_images(images, gs_id)
            else:
                log(DEMO_LOG, f"Ground Station {2001 + gs_id}: Error retrieving images: {response.text}")
        except Exception as e:
            log(DEMO_LOG, f"Ground Station {2001 + gs_id}: Error retrieving images: {e}")

def save_images(images, gs_id):
    """Save received images."""
    for image_path in images:
        try:
            file_name = os.path.basename(image_path)
            dest_path = os.path.join(RESULTS_DIR, "images", f"GS_{2001 + gs_id}_{file_name}")
            with open(image_path, "rb") as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            log(DEMO_LOG, f"Image {file_name} saved to {dest_path}")
        except Exception as e:
            log(DEMO_LOG, f"Error saving image {file_name}: {e}")

def demonstrate_time_sync():
    """Demonstrate time synchronization among satellites."""
    log(DEMO_LOG, "Demonstrating time synchronization across satellites...")
    times = []
    for sat_id in range(1, NUM_SATELLITES + 1):
        port = BASE_PORT + sat_id
        url = f"http://{BASE_IP}:{port}/get_local_time"
        try:
            response = session.get(url)
            if response.status_code == 200:
                local_time = response.json()["local_time"]
                log(DEMO_LOG, f"Satellite {sat_id}: Local time: {local_time}")
                times.append(local_time)
            else:
                log(DEMO_LOG, f"Satellite {sat_id}: Failed to retrieve local time: {response.text}")
        except Exception as e:
            log(DEMO_LOG, f"Satellite {sat_id}: Error retrieving local time: {e}")
    log(DEMO_LOG, f"Time synchronization complete. Times: {times}")

def visualize_network():
    """Visualize satellite and ground station network."""
    log(DEMO_LOG, "Visualizing the satellite-ground station network...")
    G = nx.Graph()
    G.add_nodes_from([f"Satellite {i}" for i in range(1, NUM_SATELLITES + 1)])
    G.add_nodes_from([f"Ground Station {2001 + j}" for j in range(NUM_GROUND_STATIONS)])
    for sat_id in range(1, NUM_SATELLITES + 1):
        for gs_id in range(NUM_GROUND_STATIONS):
            G.add_edge(f"Satellite {sat_id}", f"Ground Station {2001 + gs_id}")
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color="skyblue", edge_color="gray", node_size=2000, font_size=10)
    plt.title("Network Visualization")
    plt.savefig(os.path.join(RESULTS_DIR, "network_visualization.png"))
    log(DEMO_LOG, "Network visualization saved as 'network_visualization.png'.")

def demo():
    """Run the complete Astroleo demonstration."""
    prepare_directories()
    log(DEMO_LOG, "Starting the Astroleo protocol demonstration...")
    initialize_demo()

    log(DEMO_LOG, "Key exchange phase...")
    key_exchange()

    log(DEMO_LOG, "Image transmission phase...")
    capture_and_transmit_images()

    log(DEMO_LOG, "Image retrieval phase...")
    list_received_images()

    log(DEMO_LOG, "Time synchronization phase...")
    demonstrate_time_sync()

    log(DEMO_LOG, "Visualization phase...")
    visualize_network()

    log(DEMO_LOG, "Demo complete!")

if __name__ == "__main__":
    demo()
