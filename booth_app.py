import cv2
import numpy as np
import os
import time
from datetime import datetime
import qrcode

# Setup output folders for captured photos
CAPTURE_DIR = "captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

# Configuration constants
BRANDING_TEXT = "EXPO 2026 - PENCIL SKETCH BOOTH"
DEFAULT_DOWNLOAD_BASE = "http://192.168.1.100:5000/download/" # Expo server download link

# Define Filter Modes
MODES = {
    1: ("B&W Pencil Sketch", "bw_sketch"),
    2: ("Color Pencil Sketch", "color_sketch"),
    3: ("Artistic Cartoon", "cartoon"),
    4: ("Vintage Sepia Sketch", "sepia_sketch"),
    5: ("Glowing Neon Edges", "neon_edge")
}

def pencil_sketch_bw(img, blur_ksize=21):
    """
    Converts a BGR image to a high-quality grayscale pencil sketch
    using the Dodge/Burn technique: gray / (255 - blur)
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    inverted = 255 - gray
    
    # Gaussian blur kernel size MUST be odd
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blur_ksize = max(3, blur_ksize)
    
    blurred = cv2.GaussianBlur(inverted, (blur_ksize, blur_ksize), 0)
    
    # Dodge Blend division (scale=256 maps division output to full uint8 range)
    sketch_gray = cv2.divide(gray, 255 - blurred, scale=256)
    
    # Darken the pencil lines (using more black) by multiplying the sketch with itself
    sketch_gray = cv2.multiply(sketch_gray, sketch_gray, scale=1.0/255.0)
    
    # Convert back to 3-channel BGR for consistent array sizes
    return cv2.cvtColor(sketch_gray, cv2.COLOR_GRAY2BGR)

def pencil_sketch_color(img, blur_ksize=21):
    """
    Generates a color pencil sketch by applying dodge blend on grayscale 
    and combining it with original colors using a Multiply blend.
    """
    # 1. Get B&W sketch texture
    bw_sketch = pencil_sketch_bw(img, blur_ksize)
    
    # 2. Multiply original colors with sketch textures
    color_sketch = cv2.multiply(img.astype(np.float32), bw_sketch.astype(np.float32), scale=1.0/255.0)
    return np.clip(color_sketch, 0, 255).astype(np.uint8)

def cartoon_filter(img, smoothness=3, edge_thickness=9):
    """
    Bilateral color smoothing merged with adaptive threshold outlines
    to create a hand-drawn cartoon illustration style.
    """
    # 1. Bilateral filter to smooth color while keeping lines sharp
    color = img.copy()
    for _ in range(smoothness):
        color = cv2.bilateralFilter(color, d=9, sigmaColor=75, sigmaSpace=75)
        
    # 2. Convert to gray and median blur to clean outline noise
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    
    # Thickness must be odd
    if edge_thickness % 2 == 0:
        edge_thickness += 1
    edge_thickness = max(3, edge_thickness)
    
    # 3. Compute clean edges via adaptive thresholding
    edges = cv2.adaptiveThreshold(
        gray, 255, 
        cv2.ADAPTIVE_THRESH_MEAN_C, 
        cv2.THRESH_BINARY, 
        edge_thickness, 
        5
    )
    
    # 4. Mask the edges on top of the bilaterally smoothed color image
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return cv2.bitwise_and(color, edges_bgr)

def sepia_filter(img):
    """
    Applies B&W sketch textures and transforms color mapping
    into warm vintage sepia tones.
    """
    sketch = pencil_sketch_bw(img)
    # Standard Sepia transformation matrix
    sepia_matrix = np.array([
        [0.272, 0.534, 0.131],
        [0.349, 0.686, 0.168],
        [0.393, 0.769, 0.189]
    ])
    sepia = cv2.transform(sketch, sepia_matrix)
    return np.clip(sepia, 0, 255).astype(np.uint8)

def neon_edge_filter(img):
    """
    Extracts high-contrast lines via Canny edge detection and draws 
    them as fluorescent neon green strokes on a pitch-black canvas.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 95)
    
    # Dilate edges slightly to enhance visibility on large displays
    kernel = np.ones((2, 2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Create black background and map edge indices to neon green [BGR: (0, 255, 0)]
    neon = np.zeros_like(img)
    neon[edges > 0] = [0, 255, 100]
    return neon

def add_branding_overlay(img, text=BRANDING_TEXT):
    """
    Adds a premium, semi-transparent black branding bar with custom event 
    title at the bottom of the sketch output.
    """
    h, w = img.shape[:2]
    overlay = img.copy()
    bar_height = 45
    
    # Draw dark overlay strip
    cv2.rectangle(overlay, (0, h - bar_height), (w, h), (0, 0, 0), -1)
    # Blend: 70% dark strip, 30% original base
    img_blended = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)
    
    # Write event name
    cv2.putText(
        img_blended, 
        text, 
        (25, h - 15), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.55, 
        (240, 240, 240), 
        1, 
        cv2.LINE_AA
    )
    return img_blended

def generate_qr(target_url):
    """
    Generates a high-quality BGR QR code matching the URL, resized to 160x160 
    for easy canvas overlay. Returns None if generation fails.
    """
    try:
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(target_url)
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        
        # Convert PIL to BGR OpenCV image
        qr_cv = cv2.cvtColor(np.array(qr_pil), cv2.COLOR_RGB2BGR)
        return cv2.resize(qr_cv, (160, 160), interpolation=cv2.INTER_NEAREST)
    except Exception as e:
        print(f"QR Code generation failed: {e}")
        return None

def main():
    print("====================================================")
    print("  LIVE PENCIL SKETCH BOOTH - STARTING APP...")
    print("====================================================")
    print("Controls:")
    print("  [SPACE]     - Trigger Capture Countdown (3 seconds)")
    print("  [1] to [5]  - Select Filters (B&W, Color, Cartoon, Sepia, Neon)")
    print("  [S]         - Toggle Split-Screen Live Mode")
    print("  [F]         - Toggle Fullscreen / Kiosk Window mode")
    print("  [Q] / [ESC] - Quit Application")
    print("====================================================")

    # Initialize Window
    win_name = "Live Pencil Sketch Booth"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    fullscreen = True
    cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # State variables
    current_mode_id = 1
    split_screen = True
    
    # Capture states
    countdown_active = False
    countdown_start = 0
    countdown_duration = 3.0
    
    # Review capture state
    review_active = False
    review_start = 0
    review_duration = 6.0 # Show captured photo and QR code for 6 seconds
    review_image = None
    review_qr = None

    # Camera startup with connection resilience
    cap = None
    reconnect_cooldown = 0
    camera_index = 0

    while True:
        loop_start = time.time()
        
        # Safe Camera Connection / Verification
        if cap is None or not cap.isOpened():
            if time.time() - reconnect_cooldown > 3.0: # Attempt to reconnect every 3s
                reconnect_cooldown = time.time()
                print(f"Connecting to webcam index {camera_index}...")
                cap = cv2.VideoCapture(camera_index)
                if not cap.isOpened():
                    print("Camera not found. Will retry shortly...")
            
            # Show camera disconnected screen
            error_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            cv2.putText(
                error_frame, 
                "WEBCAM DISCONNECTED. CONNECTING CAMERA...", 
                (200, 360), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                1.0, 
                (50, 50, 220), 
                2, 
                cv2.LINE_AA
            )
            cv2.imshow(win_name, error_frame)
            key = cv2.waitKey(30) & 0xFF
            if key in [ord('q'), ord('Q'), 27]:
                break
            continue

        # Try reading camera frame
        try:
            ret, frame = cap.read()
            if not ret or frame is None:
                raise Exception("Empty frame received.")
        except Exception as e:
            print(f"Error reading webcam frame: {e}. Resetting connection...")
            cap.release()
            cap = None
            continue

        # Horizontal Mirroring (Selfie Mode)
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        # Apply currently active sketch filter
        mode_title, mode_key = MODES[current_mode_id]
        try:
            if mode_key == "bw_sketch":
                processed = pencil_sketch_bw(frame)
            elif mode_key == "color_sketch":
                processed = pencil_sketch_color(frame)
            elif mode_key == "cartoon":
                processed = cartoon_filter(frame)
            elif mode_key == "sepia_sketch":
                processed = sepia_filter(frame)
            elif mode_key == "neon_edge":
                processed = neon_edge_filter(frame)
            else:
                processed = frame.copy()
        except Exception as e:
            print(f"Filter processing error: {e}. Falling back to original.")
            processed = frame.copy()

        # Handle review state (display photo + QR Code)
        if review_active:
            # Check if review period is over
            if time.time() - review_start > review_duration:
                review_active = False
                review_image = None
                review_qr = None
            else:
                # Display review canvas
                canvas = review_image.copy()
                rh, rw = canvas.shape[:2]
                
                # Draw translucent banner overlay at the top
                top_banner = canvas.copy()
                cv2.rectangle(top_banner, (0, 0), (rw, 75), (0, 0, 0), -1)
                canvas = cv2.addWeighted(top_banner, 0.65, canvas, 0.35, 0)
                
                cv2.putText(
                    canvas, 
                    "SMILE SAVED! SCAN QR CODE TO DOWNLOAD", 
                    (int(rw * 0.05), 45), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 255, 100), 
                    2, 
                    cv2.LINE_AA
                )
                
                # Overlay QR Code onto bottom-right corner if available
                if review_qr is not None:
                    qrh, qrw = review_qr.shape[:2]
                    offset_y = rh - qrh - 60
                    offset_x = rw - qrw - 30
                    
                    # QR Code backing card
                    cv2.rectangle(
                        canvas, 
                        (offset_x - 10, offset_y - 10), 
                        (offset_x + qrw + 10, offset_y + qrh + 10), 
                        (0, 0, 0), 
                        -1
                    )
                    canvas[offset_y:offset_y+qrh, offset_x:offset_x+qrw] = review_qr
                    
                    cv2.putText(
                        canvas, 
                        "SCAN ME", 
                        (offset_x + 35, offset_y + qrh + 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.4, 
                        (200, 200, 200), 
                        1, 
                        cv2.LINE_AA
                    )
                
                cv2.imshow(win_name, canvas)
                
                # Check for exit during review
                key = cv2.waitKey(20) & 0xFF
                if key in [ord('q'), ord('Q'), 27]:
                    break
                elif key == ord('f') or key == ord('F'):
                    fullscreen = not fullscreen
                    cv2.setWindowProperty(
                        win_name, 
                        cv2.WND_PROP_FULLSCREEN, 
                        cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
                    )
                continue

        # Split screen or Single filter render
        if split_screen:
            # Scale BGR frame and processed sketch to fit side-by-side
            half_w = w // 2
            original_half = cv2.resize(frame, (half_w, h))
            processed_half = cv2.resize(processed, (half_w, h))
            
            # Combine original on left, filter sketch on right
            display_frame = np.hstack((original_half, processed_half))
            # Draw dividing center line
            cv2.line(display_frame, (half_w, 0), (half_w, h), (0, 255, 255), 2)
        else:
            display_frame = processed.copy()

        # Handle photo capture countdown
        if countdown_active:
            elapsed = time.time() - countdown_start
            remaining = int(np.ceil(countdown_duration - elapsed))
            
            if remaining <= 0:
                # Trigger photo flash rendering overlay
                flash = np.ones_like(display_frame) * 255
                cv2.imshow(win_name, flash)
                cv2.waitKey(120)
                
                # Save the final styled sketch with event branding
                final_saved = add_branding_overlay(processed)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sketch_{timestamp}.jpg"
                filepath = os.path.join(CAPTURE_DIR, filename)
                
                # Save image
                cv2.imwrite(filepath, final_saved)
                print(f"Captured photo saved successfully: {filepath}")
                
                # Generate QR code for download
                download_url = f"{DEFAULT_DOWNLOAD_BASE}{filename}"
                review_qr = generate_qr(download_url)
                
                # Switch to review state
                countdown_active = False
                review_active = True
                review_start = time.time()
                review_image = final_saved
                continue
            else:
                # Draw large circular progress countdown in screen center
                cx, cy = display_frame.shape[1] // 2, display_frame.shape[0] // 2
                cv2.circle(display_frame, (cx, cy), 80, (0, 0, 0), -1)
                cv2.circle(display_frame, (cx, cy), 80, (255, 255, 0), 3)
                
                cv2.putText(
                    display_frame, 
                    str(remaining), 
                    (cx - 22, cy + 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    2.8, 
                    (0, 255, 255), 
                    6, 
                    cv2.LINE_AA
                )

        # Draw UI overlay header and control keys
        cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 45), (10, 10, 10), -1)
        cv2.putText(
            display_frame,
            f"Mode: {mode_title} | [SPACE] Capture | [1-5] Filters | [S] Split Toggle | [Q] Quit",
            (20, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Show final frame
        cv2.imshow(win_name, display_frame)

        # Cap processing loop at ~25 FPS to save system load
        elapsed_loop = time.time() - loop_start
        delay = max(1, int((0.04 - elapsed_loop) * 1000))
        
        # Keyboard polling
        key = cv2.waitKey(delay) & 0xFF
        if key in [ord('q'), ord('Q'), 27]: # ESC or Q to quit
            break
        elif key == ord(' '): # SPACE to start countdown
            if not countdown_active and not review_active:
                countdown_active = True
                countdown_start = time.time()
        elif key == ord('s') or key == ord('S'):
            split_screen = not split_screen
        elif key == ord('f') or key == ord('F'):
            fullscreen = not fullscreen
            cv2.setWindowProperty(
                win_name, 
                cv2.WND_PROP_FULLSCREEN, 
                cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL
            )
        elif ord('1') <= key <= ord('5'):
            current_mode_id = key - ord('0')

    # Release resources on exit
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Live Pencil Sketch Booth exited successfully.")

if __name__ == "__main__":
    main()
