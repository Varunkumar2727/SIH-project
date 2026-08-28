import cv2
import numpy as np
from PIL import Image


def load_image_cv(image_path: str) -> np.ndarray:
    """Loads an image using OpenCV or PIL (supports PNG, JPG, TIFF)."""
    # OpenCV imread doesn't support 16-bit GeoTIFF multi-band directly well without flags
    img = cv2.imread(image_path)
    if img is None:
        # Fallback to PIL then convert to BGR array
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img


def preprocess_image(img_bgr: np.ndarray):
    """
    Preprocesses satellite image for segmentation:
    - Gaussian Denoising
    - HSV color space conversion
    - Grayscale + Contrast Adjustment (CLAHE)
    - Canny Edge Map
    """
    # Denoise
    blurred = cv2.GaussianBlur(img_bgr, (5, 5), 0)

    # HSV conversion
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Grayscale & CLAHE contrast boost
    gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)

    # Edge map
    edges = cv2.Canny(enhanced_gray, 50, 150)

    return {
        "bgr": img_bgr,
        "blurred": blurred,
        "hsv": hsv,
        "gray": enhanced_gray,
        "edges": edges
    }
