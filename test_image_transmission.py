import requests
import time
import hashlib
import os

session = requests.Session()
session.trust_env = False

# Endpoints
SATELLITE_BASE_URL = "http://10.35.70.23:5001"  # Update with the actual satellite node's port
GROUND_STATION_BASE_URL = "http://10.35.70.23:6001"  # Update with the actual ground station's port

def calculate_file_hash(file_path):
    """
    Calculate the SHA256 hash of a file.
    :param file_path: Path to the file.
    :return: SHA256 hash as a hexadecimal string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def test_capture_and_transmit_image():
    """
    Test the process of capturing an image on the satellite, transmitting it to the ground station, 
    and verifying its integrity.
    """

    # Step 1: Capture and transmit the image from the satellite
    print("Step 1: Capturing and transmitting image from the satellite...")
    response = session.post(f"{SATELLITE_BASE_URL}/capture_image")
    if response.status_code != 200:
        print(f"Failed to capture and transmit image: {response.json()}")
        return
    response_data = response.json()
    image_path = response_data.get("image_path")
    dest_id = response_data.get("dest_id")

    print(f"Image captured and transmitted successfully.")
    print(f"Source image path: {image_path}, Destination ID: {dest_id}")

    # Step 2: Calculate the hash of the source image
    original_image_hash = calculate_file_hash(image_path)
    print(f"Original image hash: {original_image_hash}")

    # Step 3: Wait briefly to ensure ground station processes the image
    time.sleep(2)

    # Step 4: Verify the image was received by the ground station
    print("Step 4: Verifying the image was received by the ground station...")
    response = session.get(f"{GROUND_STATION_BASE_URL}/get_received_images")
    if response.status_code != 200:
        print(f"Failed to retrieve received images from ground station: {response.json()}")
        return

    images = response.json().get("images", [])
    if not images:
        print("No images received by the ground station.")
        return

    print(f"Images received by the ground station: {images}")

    # Step 5: Compare the hash of the received image with the original
    received_image_path = images[-1]  # Assuming the last image is the most recent one
    print(f"Received image path: {received_image_path}")

    try:
        received_image_hash = calculate_file_hash(received_image_path)
        print(f"Received image hash: {received_image_hash}")

        if original_image_hash == received_image_hash:
            print("Test passed: The received image matches the original.")
        else:
            print("Test failed: The received image does not match the original.")
    except Exception as e:
        print(f"Failed to calculate hash of the received image: {e}")

if __name__ == "__main__":
    # Run the test
    test_capture_and_transmit_image()
