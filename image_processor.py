import cv2
import numpy as np

def adjust_brightness_contrast(image, brightness=0, contrast=0):
    """
    Adjusts brightness and contrast of an image.
    brightness range: -100 to 100
    contrast range: -100 to 100
    """
    # Convert to float for math operations
    buf = image.astype(np.int32)
    
    if brightness != 0:
        buf = buf + brightness
        
    if contrast != 0:
        # Map contrast from [-100, 100] to scale factor [0.5, 3.0]
        # 0 contrast -> scale factor 1.0
        # -100 contrast -> scale factor 0.3
        # 100 contrast -> scale factor 3.0
        if contrast > 0:
            factor = 1.0 + (contrast / 50.0)
        else:
            factor = 1.0 + (contrast / 130.0) # avoid division by zero or negative
        
        mean = np.mean(buf)
        buf = (buf - mean) * factor + mean
        
    buf = np.clip(buf, 0, 255).astype(np.uint8)
    return buf

def apply_cartoon(img, smoothness=4, edge_thickness=9, edge_strength=5):
    """
    Applies a cartoon/cell-shaded effect.
    - smoothness: number of bilateral filter iterations (1-10)
    - edge_thickness: adaptive threshold block size (must be odd, 3-25)
    - edge_strength: adaptive threshold constant to subtract (1-20)
    """
    # 1. Bilateral filter to smooth color while keeping edges
    color = img.copy()
    for _ in range(int(smoothness)):
        color = cv2.bilateralFilter(color, d=9, sigmaColor=75, sigmaSpace=75)
    
    # 2. Convert to grayscale and apply median blur for clean lines
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    
    # 3. Detect edges using adaptive threshold
    # Block size must be odd and >= 3
    block_size = int(edge_thickness)
    if block_size % 2 == 0:
        block_size += 1
    block_size = max(3, block_size)
    
    edges = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_MEAN_C, 
        cv2.THRESH_BINARY, 
        block_size, 
        int(edge_strength)
    )
    
    # 4. Merge edges with smoothed color image
    edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(color, edges_color)
    return cartoon

def apply_watercolor(img, brush_size=60, smoothing=0.3):
    """
    Applies a watercolor effect using OpenCV's stylization.
    - brush_size (sigma_s): 0 to 200
    - smoothing (sigma_r): 0.0 to 1.0
    """
    # Ensure parameters are in range
    s = float(brush_size)
    r = float(smoothing)
    
    # cv2.stylization works on 3-channel images and performs non-photorealistic rendering
    res = cv2.stylization(img, sigma_s=s, sigma_r=r)
    return res

def apply_oil_painting(img, brush_size=4, intensity=3):
    """
    Applies an oil painting effect.
    Attempts to use cv2.xphoto.oilPainting if available (opencv-contrib-python).
    Otherwise, falls back to a custom color quantization + bilateral filter palette knife effect.
    - brush_size: 1 to 15
    - intensity: 1 to 20
    """
    # Try using cv2.xphoto.oilPainting
    try:
        # Check if attribute exists
        if hasattr(cv2, 'xphoto') and hasattr(cv2.xphoto, 'oilPainting'):
            return cv2.xphoto.oilPainting(img, int(brush_size), int(intensity))
    except Exception:
        pass
        
    # Fallback: Palette Knife effect using K-Means and Bilateral filtering
    return apply_palette_knife(img, colors=int(intensity) + 3, smoothness=int(brush_size))

def apply_palette_knife(img, colors=8, smoothness=5):
    """
    Simulates a palette knife painting by combining K-means color quantization, 
    bilateral filtering, and edge enhancement.
    - colors: K-Means clusters (3 to 32)
    - smoothness: filter passes (1 to 10)
    """
    colors = max(3, min(32, colors))
    smoothness = max(1, min(10, smoothness))
    
    # 1. Bilateral filter to simplify regions
    smoothed = img.copy()
    for _ in range(smoothness):
        smoothed = cv2.bilateralFilter(smoothed, d=9, sigmaColor=80, sigmaSpace=80)
        
    # 2. Reshape image to list of pixels for K-means
    data = smoothed.reshape((-1, 3)).astype(np.float32)
    
    # 3. Perform K-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(data, colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # 4. Reconstruct image from cluster centers
    centers = np.uint8(centers)
    quantized = centers[labels.flatten()]
    quantized = quantized.reshape(smoothed.shape)
    
    # 5. Slightly enhance details for a more artistic look
    detail = cv2.detailEnhance(quantized, sigma_s=10, sigma_r=0.15)
    return detail

def apply_pencil_sketch(img, brush_size=60, smoothing=0.07, shade_factor=0.03, color=False):
    """
    Applies a pencil sketch effect.
    - brush_size (sigma_s): 0 to 200
    - smoothing (sigma_r): 0.0 to 1.0
    - shade_factor: 0.0 to 0.1
    - color: True for color pencil sketch, False for grayscale
    """
    s = float(brush_size)
    r = float(smoothing)
    sf = float(shade_factor)
    
    sketch_gray, sketch_color = cv2.pencilSketch(img, sigma_s=s, sigma_r=r, shade_factor=sf)
    
    if color:
        return sketch_color
    else:
        # Convert grayscale back to 3-channel BGR so output shape is consistent
        return cv2.cvtColor(sketch_gray, cv2.COLOR_GRAY2BGR)
