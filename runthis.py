import requests
import os

# Get the full path to the JSON file
json_file_path = os.path.abspath('./playlist_genres.json')
print(f"Looking for file at: {json_file_path}")
print(f"File exists: {os.path.exists(json_file_path)}")

# Test the API with absolute path
response = requests.post('http://localhost:8000/analyze-playlist-json', 
    json={'file_path': json_file_path}
)

if response.status_code == 200:
    result = response.json()
    print(f"Your vibe: {result['user_display']['vibe_name']}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)