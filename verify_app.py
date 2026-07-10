import requests
import os

def test_api():
    base_url = 'http://127.0.0.1:5000'
    image_path = 'test_real.jpg'
    
    if not os.path.exists(image_path):
        print(f"Error: {image_path} does not exist.")
        return False
        
    print("--- 1. Testing Upload ---")
    files = {'image': open(image_path, 'rb')}
    try:
        r = requests.post(f"{base_url}/upload", files=files)
        if r.status_code != 200:
            print(f"Upload failed: {r.status_code} - {r.text}")
            return False
            
        data = r.json()
        file_id = data['file_id']
        orig_url = data['original_url']
        print(f"Upload successful. file_id: {file_id}, original_url: {orig_url}")
        
    except Exception as e:
        print(f"Error during upload: {e}")
        return False
        
    print("\n--- 2. Testing Watercolor Processing ---")
    payload = {
        'file_id': file_id,
        'style': 'watercolor',
        'brush_size': 60,
        'smoothing': 0.3,
        'brightness': 0,
        'contrast': 0
    }
    try:
        r = requests.post(f"{base_url}/process", json=payload)
        if r.status_code != 200:
            print(f"Processing failed: {r.status_code} - {r.text}")
            return False
            
        proc_data = r.json()
        print(f"Watercolor processing successful. URL: {proc_data['processed_url']}")
        
    except Exception as e:
        print(f"Error during watercolor processing: {e}")
        return False

    print("\n--- 3. Testing Oil Painting Processing with Custom Params ---")
    payload = {
        'file_id': file_id,
        'style': 'oil',
        'brush_size': 5,
        'intensity': 4,
        'brightness': 15,
        'contrast': -10
    }
    try:
        r = requests.post(f"{base_url}/process", json=payload)
        if r.status_code != 200:
            print(f"Oil processing failed: {r.status_code} - {r.text}")
            return False
            
        proc_data = r.json()
        print(f"Oil painting processing successful. URL: {proc_data['processed_url']}")
        
    except Exception as e:
        print(f"Error during oil processing: {e}")
        return False
        
    print("\n--- 4. Testing Cartoon Processing ---")
    payload = {
        'file_id': file_id,
        'style': 'cartoon',
        'smoothness': 3,
        'edge_thickness': 7,
        'edge_strength': 4,
        'brightness': 0,
        'contrast': 10
    }
    try:
        r = requests.post(f"{base_url}/process", json=payload)
        if r.status_code != 200:
            print(f"Cartoon processing failed: {r.status_code} - {r.text}")
            return False
            
        proc_data = r.json()
        print(f"Cartoon processing successful. URL: {proc_data['processed_url']}")
        
    except Exception as e:
        print(f"Error during cartoon processing: {e}")
        return False

    print("\n--- 5. Testing Pencil Color Sketch ---")
    payload = {
        'file_id': file_id,
        'style': 'pencil_color',
        'brush_size': 50,
        'smoothing': 0.08,
        'shade_factor': 0.04,
        'brightness': 0,
        'contrast': 0
    }
    try:
        r = requests.post(f"{base_url}/process", json=payload)
        if r.status_code != 200:
            print(f"Pencil color processing failed: {r.status_code} - {r.text}")
            return False
            
        proc_data = r.json()
        print(f"Pencil color processing successful. URL: {proc_data['processed_url']}")
        
    except Exception as e:
        print(f"Error during pencil color processing: {e}")
        return False

    print("\n--- 6. Testing AI Image Generation ---")
    payload = {
        'prompt': 'A scenic oil painting of a castle on a hill'
    }
    try:
        r = requests.post(f"{base_url}/generate", json=payload)
        if r.status_code == 400 and 'configure it to enable' in r.text:
            print("AI image generation skipped: GEMINI_API_KEY environment variable is not configured.")
        elif r.status_code != 200:
            print(f"AI generation failed: {r.status_code} - {r.text}")
            return False
        else:
            gen_data = r.json()
            print(f"AI image generation successful. file_id: {gen_data['file_id']}, URL: {gen_data['original_url']}")
            
            # Now let's try processing this AI generated image
            print("\n--- 7. Testing Watercolor Processing on AI Generated Image ---")
            payload = {
                'file_id': gen_data['file_id'],
                'style': 'watercolor',
                'brush_size': 50,
                'smoothing': 0.3,
                'brightness': 0,
                'contrast': 0
            }
            r = requests.post(f"{base_url}/process", json=payload)
            if r.status_code != 200:
                print(f"Watercolor processing on AI image failed: {r.status_code} - {r.text}")
                return False
            proc_data = r.json()
            print(f"Watercolor processing on AI image successful. URL: {proc_data['processed_url']}")
            
    except Exception as e:
        print(f"Error during AI image generation testing: {e}")
        return False

    print("\nAll Backend Pipeline Tests Passed successfully!")
    return True

if __name__ == '__main__':
    test_api()
