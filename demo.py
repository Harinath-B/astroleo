import os
import time
from threading import Thread
from utils.logging_utils import setup_logger
import requests
from random import randint
from hashlib import sha256

logger = setup_logger("demo", "demo")

BASE_IP = "10.35.70.23"
PORT_BASE = 5000
NUM_SATELLITES = 5
GROUND_STATIONS = 2
LAUNCH_DELAY = 3  
RESULTS_DIR = "demo_results"

session = requests.Session()
session.trust_env = False

def log(message):
    logger.info(message)

def setup_results_dir():

    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(f"{RESULTS_DIR}/images", exist_ok=True)

def launch_node(node_id, x, y, z, node_type):

    node_type_name = "Satellite" if node_type == 0 else "Ground Station"
    log(f"Launching {node_type_name} {node_id} at position ({x}, {y}, {z}).")
    Thread(target=lambda: os.system(
        f"python3 main.py {node_id} {x} {y} {z} {node_type}"
    )).start()
    time.sleep(LAUNCH_DELAY)

def initialize_nodes():

    log("Launching satellite nodes and ground stations...")   
    for i in range(1, NUM_SATELLITES + 1):
        launch_node(i, randint(0, 10), randint(0, 10), randint(0, 10), 0)    
    for j in range(GROUND_STATIONS):
        launch_node(1001 + j, randint(0, 10), randint(0, 10), 0, 1)

    log("Nodes and stations launched.")

def perform_key_exchange():

    log("Performing key exchange...")

    for gs_id in range(1001, 1001 + GROUND_STATIONS):
        gs_port = PORT_BASE + gs_id
        gs_url = f"http://{BASE_IP}:{gs_port}/broadcast_key"
        for sat_id in range(1, NUM_SATELLITES + 1):
            sat_port = PORT_BASE + sat_id
            sat_url = f"http://{BASE_IP}:{sat_port}/broadcast_key"
            
            try:
                session.post(gs_url, json={"neighbor_id": sat_id})
                log(f"Ground Station {gs_id} broadcasted key to Satellite {sat_id}.")
            except Exception as e:
                log(f"Ground Station {gs_id}: Key broadcast error: {e}")

            
            try:
                session.post(sat_url, json={"neighbor_id": gs_id})
                log(f"Satellite {sat_id} broadcasted key to Ground Station {gs_id}.")
            except Exception as e:
                log(f"Satellite {sat_id}: Key broadcast error: {e}")

    log("Key exchange completed.")

def capture_and_transmit_images():

    log("Capturing and transmitting images from satellites...")
    for sat_id in range(1, NUM_SATELLITES + 1):
        capture_url = f"http://{BASE_IP}:{PORT_BASE + sat_id}/capture_image"
        try:
            response = session.post(capture_url)
            if response.status_code == 200:
                log(f"Satellite {sat_id}: Image captured and transmitted successfully.")
            else:
                log(f"Satellite {sat_id}: Failed to capture and transmit image: {response.text}")
        except Exception as e:
            log(f"Satellite {sat_id}: Error during image capture: {e}")

def retrieve_images():

    log("Retrieving received images from ground stations...")
    for gs_id in range(1001, 1001 + GROUND_STATIONS):
        gs_port = PORT_BASE + gs_id
        url = f"http://{BASE_IP}:{gs_port}/get_received_images"
        try:
            response = session.get(url)
            if response.status_code == 200:
                images = response.json()["images"]
                log(f"Ground Station {gs_id}: Images retrieved: {images}")
                save_images_to_results(gs_id, images)
            else:
                log(f"Ground Station {gs_id}: Error retrieving images: {response.text}")
        except Exception as e:
            log(f"Ground Station {gs_id}: Error retrieving images: {e}")

def save_images_to_results(gs_id, images):

    for image_path in images:
        try:
            with open(image_path, "rb") as img_file:
                data = img_file.read()
                checksum = sha256(data).hexdigest()
                dest_path = f"{RESULTS_DIR}/images/gs_{gs_id}_{os.path.basename(image_path)}"
                with open(dest_path, "wb") as dest_file:
                    dest_file.write(data)
                log(f"Image {image_path} saved to {dest_path} with checksum {checksum}.")
        except Exception as e:
            log(f"Error saving image {image_path}: {e}")

def demonstrate_time_sync():

    log("Demonstrating time synchronization across satellites...")
    times = {}
    for sat_id in range(1, NUM_SATELLITES + 1):
        url = f"http://{BASE_IP}:{PORT_BASE + sat_id}/get_local_time"
        try:
            response = session.get(url)
            if response.status_code == 200:
                local_time = response.json()["local_time"]
                times[sat_id] = local_time
                log(f"Satellite {sat_id}: Local time: {local_time}")
            else:
                log(f"Satellite {sat_id}: Failed to retrieve local time: {response.text}")
        except Exception as e:
            log(f"Satellite {sat_id}: Error retrieving local time: {e}")

def demo():

    setup_results_dir()
    log("Starting Astroleo Protocol Demo...")

    initialize_nodes()
    perform_key_exchange()
    capture_and_transmit_images()
    retrieve_images()
    demonstrate_time_sync()

    log("Demo complete. Results saved in the 'demo_results' directory.")

if __name__ == "__main__":
    demo()
