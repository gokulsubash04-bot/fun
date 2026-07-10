import os
import uuid
import time
from flask import Flask, render_template, request, jsonify, url_for
import cv2
import numpy as np

# Import our image processor
import image_processor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)

def cleanup_old_files():
    """Delete files in the upload directory that are older than 10 minutes."""
    try:
        now = time.time()
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(filepath):
                # Check if it's older than 600 seconds
                if os.stat(filepath).st_mtime < now - 600:
                    os.remove(filepath)
    except Exception as e:
        print(f"Error during file cleanup: {e}")

@app.route('/')
def index():
    cleanup_old_files()
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    cleanup_old_files()
    
    if 'image' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    # Generate a unique filename prefix
    file_id = str(uuid.uuid4())
    original_filename = f"orig_{file_id}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    
    # Save the file
    file.save(filepath)
    
    # Read the image and downscale if it's extremely large to keep processing responsive
    try:
        img = cv2.imread(filepath)
        if img is None:
            os.remove(filepath)
            return jsonify({'error': 'Invalid image format'}), 400
            
        h, w = img.shape[:2]
        max_dim = 1600
        if max(h, w) > max_dim:
            # Downscale preserving aspect ratio
            scale = max_dim / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            cv2.imwrite(filepath, img)
            
        return jsonify({
            'file_id': file_id,
            'original_url': url_for('static', filename=f"images/{original_filename}"),
            'width': img.shape[1],
            'height': img.shape[0]
        })
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': f'Failed to process upload: {str(e)}'}), 500

@app.route('/process', methods=['POST'])
def process_image():
    cleanup_old_files()
    
    data = request.json or {}
    file_id = data.get('file_id')
    style = data.get('style', 'watercolor')
    
    if not file_id:
        return jsonify({'error': 'Missing file_id'}), 400
        
    original_filename = f"orig_{file_id}.jpg"
    original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
    
    if not os.path.exists(original_path):
        return jsonify({'error': 'Original image has expired or does not exist'}), 404
        
    # Read the image
    img = cv2.imread(original_path)
    if img is None:
        return jsonify({'error': 'Could not read original image'}), 500
        
    # Read parameters from post request
    brightness = int(data.get('brightness', 0))
    contrast = int(data.get('contrast', 0))
    
    # Pre-adjust brightness and contrast
    img_adjusted = image_processor.adjust_brightness_contrast(img, brightness, contrast)
    
    # Process image based on chosen style
    try:
        if style == 'watercolor':
            brush_size = float(data.get('brush_size', 60))
            smoothing = float(data.get('smoothing', 0.3))
            processed = image_processor.apply_watercolor(img_adjusted, brush_size, smoothing)
            
        elif style == 'oil':
            brush_size = int(data.get('brush_size', 4))
            intensity = int(data.get('intensity', 3))
            processed = image_processor.apply_oil_painting(img_adjusted, brush_size, intensity)
            
        elif style == 'cartoon':
            smoothness = int(data.get('smoothness', 4))
            edge_thickness = int(data.get('edge_thickness', 9))
            edge_strength = int(data.get('edge_strength', 5))
            processed = image_processor.apply_cartoon(img_adjusted, smoothness, edge_thickness, edge_strength)
            
        elif style == 'pencil_color':
            brush_size = float(data.get('brush_size', 60))
            smoothing = float(data.get('smoothing', 0.07))
            shade_factor = float(data.get('shade_factor', 0.03))
            processed = image_processor.apply_pencil_sketch(img_adjusted, brush_size, smoothing, shade_factor, color=True)
            
        elif style == 'pencil_gray':
            brush_size = float(data.get('brush_size', 60))
            smoothing = float(data.get('smoothing', 0.07))
            shade_factor = float(data.get('shade_factor', 0.03))
            processed = image_processor.apply_pencil_sketch(img_adjusted, brush_size, smoothing, shade_factor, color=False)
            
        elif style == 'palette_knife':
            colors = int(data.get('colors', 8))
            smoothness = int(data.get('smoothness', 5))
            processed = image_processor.apply_palette_knife(img_adjusted, colors, smoothness)
            
        else:
            return jsonify({'error': 'Invalid painting style'}), 400
            
        # Save processed image
        processed_filename = f"proc_{file_id}_{style}.jpg"
        processed_path = os.path.join(app.config['UPLOAD_FOLDER'], processed_filename)
        cv2.imwrite(processed_path, processed)
        
        return jsonify({
            'processed_url': url_for('static', filename=f"images/{processed_filename}")
        })
    except Exception as e:
        return jsonify({'error': f'Image processing failed: {str(e)}'}), 500

@app.route('/generate', methods=['POST'])
def generate_image_ai():
    cleanup_old_files()
    
    data = request.json or {}
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
        
    # Retrieve API Key
    api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return jsonify({
            'error': 'GEMINI_API_KEY environment variable is not set. Please configure it to enable AI image generation.'
        }), 400
        
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        file_id = str(uuid.uuid4())
        original_filename = f"orig_{file_id}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        
        # Try the latest recommended model gemini-2.5-flash-image
        try:
            print("Attempting to generate image using gemini-2.5-flash-image...")
            response = client.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=prompt
            )
            image_data = None
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_data = part.inline_data.data
                        break
            
            if image_data:
                with open(filepath, 'wb') as f:
                    f.write(image_data)
            else:
                raise Exception("No inline image data found in response candidates.")
                
        except Exception as e:
            # Fallback to imagen-3.0-generate-002
            print(f"Primary model gemini-2.5-flash-image failed: {e}. Trying fallback model imagen-3.0-generate-002...")
            response = client.models.generate_images(
                model='imagen-3.0-generate-002',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type='image/jpeg'
                )
            )
            if response.generated_images:
                response.generated_images[0].image.save(filepath)
            else:
                raise Exception("Fallback image generation returned empty results.")

        # Read dimensions of the generated image
        img = cv2.imread(filepath)
        if img is None:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': 'Generated image is invalid or empty'}), 500
            
        return jsonify({
            'file_id': file_id,
            'original_url': url_for('static', filename=f"images/{original_filename}"),
            'width': img.shape[1],
            'height': img.shape[0]
        })
        
    except Exception as e:
        return jsonify({'error': f'AI Image generation failed: {str(e)}'}), 500


if __name__ == '__main__':
    # Make sure static directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
