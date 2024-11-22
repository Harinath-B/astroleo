import requests
import os

session = requests.Session()
session.trust_env = False

BASE_URL = "http://10.35.70.23:5002"  # Replace with your server's address

def test_capture_image():
    """Test the /capture_image endpoint."""
    print("Testing image capture...")
    response = session.post(f"{BASE_URL}/capture_image")
    if response.status_code == 200:
        print("Image captured successfully:", response.json())
        return response.json().get("image_path")
    else:
        print("Failed to capture image:", response.json())
        return None

def test_transmit_image(dest_id, image_path):
    """Test the /transmit_image endpoint."""
    print("Testing image transmission...")
    data = {
        "dest_id": dest_id,
        "image_path": image_path
    }
    response = session.post(f"{BASE_URL}/transmit_image", json=data)
    if response.status_code == 200:
        print("Image transmitted successfully:", response.json())
    else:
        print("Failed to transmit image:", response.json())

def test_get_received_images():
    """Test the /get_received_images endpoint."""
    print("Testing received images retrieval...")
    response = session.get(f"http://10.35.70.23:5002/get_received_images")
    if response.status_code == 200:
        print("Received images:", response.json())
    else:
        print("Failed to retrieve received images:", response.json())

# Perform the tests
if __name__ == "__main__":
    # Step 1: Test image capture
    image_path = test_capture_image()

    # Step 2: Transmit the image to a dummy node (assuming node 1 exists)
    if image_path:
        test_transmit_image(dest_id=3, image_path=image_path)

    # Step 3: Retrieve received images
    test_get_received_images()
