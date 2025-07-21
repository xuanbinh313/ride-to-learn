import requests
import json

# The URL where your Whisper web service is running
whisper_url = "http://localhost:9000/asr"

# The path to the audio file you want to transcribe
audio_file_path = "../assets/Actual Test 04.mp3"  # 👈 Change this to your file's path

# These parameters match the ones from your working curl command
params = {
    "encode": "true",
    "task": "transcribe",
    "language": "en",
    "output": "json"  # We'll ask for JSON to make it easy to parse
}

try:
    # Open the audio file in binary read mode
    with open(audio_file_path, "rb") as audio_file:
        
        # The web service expects the file in a multipart/form-data field named 'audio_file'
        files = {"audio_file": audio_file}

        print(f"🔄 Sending '{audio_file_path}' to Whisper for transcription...")

        # Send the POST request with both the file and the URL parameters
        response = requests.post(whisper_url, params=params, files=files)

        # Raise an exception if the request returned an HTTP error (like 404 or 500)
        response.raise_for_status()
        response_data = response.json()
        # save json to file
        json_file_path = "output.json"  # 👈 Change this to your desired output file path
        # save pretty JSON  
        with open(json_file_path, "w") as json_file:
            json.dump(response_data, json_file, indent=4)

except FileNotFoundError:
    print(f"❌ ERROR: The file was not found at '{audio_file_path}'")
except requests.exceptions.RequestException as e:
    print(f"❌ ERROR: There was an issue with the request. Details: {e}")