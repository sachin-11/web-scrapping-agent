import os
import base64
import requests
import logging
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def download_images(image_urls: list, product_name: str, output_folder: str = None) -> list:
    """
    Downloads list of image URLs, resizes them to max 500x500 preserving aspect ratio,
    saves them as productname_1.jpg, productname_2.jpg, etc., and returns local file paths.
    """
    saved_paths = []
    
    # If no output folder specified, default to /backend/outputs/images/
    if not output_folder:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_folder = os.path.join(backend_dir, "outputs", "images")
        
    # Create the output folder automatically
    os.makedirs(output_folder, exist_ok=True)
    
    # Clean product name to prevent filesystem issues
    safe_product_name = "".join(c for c in product_name if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    
    saved_count = 0
    for i, url in enumerate(image_urls):
        try:
            logger.info(f"Downloading image {i+1}: {url}")
            # Request image with 10s timeout
            response = requests.get(url, timeout=10)
            
            # Skip non-200 or non-image responses silently
            if response.status_code != 200:
                logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
                continue
                
            # Verify it is an image
            content_type = response.headers.get("Content-Type", "")
            if "image" not in content_type and not any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                logger.warning(f"URL does not appear to be an image: {url} (Content-Type: {content_type})")
                continue
                
            # Load image using Pillow
            image_data = BytesIO(response.content)
            img = Image.open(image_data)
            
            # Convert to RGB mode if it is RGBA or palette (P) to support saving as JPEG
            if img.mode in ("RGBA", "LA", "P"):
                # Create a white background if RGBA to preserve transparency readability
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "RGBA":
                    background.paste(img, mask=img.split()[3]) # 3 is the alpha channel
                else:
                    background.paste(img.convert("RGBA"), mask=img.convert("RGBA").split()[3])
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Resize image to max 500x500 while preserving aspect ratio
            img.thumbnail((500, 500), Image.Resampling.LANCZOS)
            
            # Define output path
            saved_count += 1
            filename = f"{safe_product_name}_{saved_count}.jpg"
            file_path = os.path.join(output_folder, filename)
            
            # Save as JPEG
            img.save(file_path, "JPEG", quality=85)
            logger.info(f"Successfully saved and resized: {file_path}")
            saved_paths.append(file_path)
            
        except Exception as e:
            # Skip broken image URLs silently as requested
            logger.error(f"Error handling image URL {url}: {e}")
            continue
            
    return saved_paths

def get_image_as_base64(image_path: str) -> str:
    """
    Reads a local image file and encodes it to a base64 string
    suitable for feeding into OpenAI Vision APIs.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at path: {image_path}")
        
    # Determine the mime type (usually jpeg in our system)
    ext = os.path.splitext(image_path)[1].lower().replace(".", "")
    if ext == "jpg":
        ext = "jpeg"
        
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
    return f"data:image/{ext};base64,{encoded_string}"
