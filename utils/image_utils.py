import os
import time
from PIL import Image

def capture_image(image_dir="images"):
    """Capture or simulate an image."""
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    image_name = f"astro_image_{int(time.time())}.png"
    image_path = os.path.join(image_dir, image_name)

    img = Image.new('RGB', (1024, 1024), color=(0, 0, 255))
    img.save(image_path)
    return image_path