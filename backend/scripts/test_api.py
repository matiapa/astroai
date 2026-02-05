import requests
import json
import os
import sys

def test_analyze(image_path, language="es", server_url="http://localhost:8000/analyze"):
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return

    print(f"Reading image from {image_path}...")
    
    # Prepare multipart form data
    with open(image_path, "rb") as f:
        files = {"image": (os.path.basename(image_path), f, "image/png")}
        data = {"language": language}
        
    print(f"Sending request to {server_url} (language: {language})...")
    try:
        response = requests.post(
            server_url,
            files=files,
            data=data,
            stream=True,  # Enable streaming
            timeout=180
        )
        
        if response.status_code == 200:
            print("Connected! Waiting for events...")
            result = None
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("event:"):
                        event_name = decoded_line.split(":", 1)[1].strip()
                        print(f"\n[EVENT] {event_name}")
                    elif decoded_line.startswith("data:"):
                        data_content = decoded_line.split(":", 1)[1].strip()
                        if event_name == "analysis_finished":
                            print("Analysis finished! Parsing result...")
                            result = json.loads(data_content)
                            break
                        else:
                            print(f"Data: {data_content}")

            if result:
                # Print summary
                print("\nAnalysis Summary:")
                print(f"Success: {result['success']}")
                if result.get('plate_solving'):
                    ps = result['plate_solving']
                    print(f"Plate Solving: RA={ps['center_ra_deg']}, DEC={ps['center_dec_deg']}")
                
                if result.get('narration'):
                    narr = result['narration']
                    print(f"Title: {narr['title']}")
                    print(f"Text: {narr['text'][:100]}...")
                    print(f"Audio URL: {narr['audio_url']}")
                    
                    # Download audio
                    audio_response = requests.get(narr['audio_url'])
                    if audio_response.status_code == 200:
                        with open("test_output_audio.wav", "wb") as af:
                            af.write(audio_response.content)
                        print("Audio downloaded to test_output_audio.wav")
                
                if result.get('identified_objects'):
                    print(f"Identified {len(result['identified_objects'])} objects.")
                    for obj in result['identified_objects'][:3]:
                        print(f"- {obj['name']} ({obj['type']}): {obj.get('legend', 'No legend')[:80]}...")
                
                # Save full response
                with open("test_response.json", "w") as f:
                    json.dump(result, f, indent=2)
                print("Full response saved to test_response.json")
            else:
                 print("Stream finished but no result found.")
                
        else:
            print(f"Error: Server returned status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error sending request: {e}")

if __name__ == "__main__":
    language = "es"
    if len(sys.argv) > 1:
        img_path = sys.argv[1]
    else:
        img_path = None
        for root, dirs, files in os.walk("logs"):
            if "captured.png" in files:
                img_path = os.path.join(root, "captured.png")
                break
        if not img_path:
            print("Please provide a path to an image file.")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        language = sys.argv[2]
            
    test_analyze(img_path, language)
