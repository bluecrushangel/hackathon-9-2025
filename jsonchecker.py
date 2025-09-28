import json

# Check the actual content of the file
try:
    with open('F:\\Personal Projects\\hackathon-9-2025\\playlist_genres.json', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("File content (first 500 chars):")
    print(content[:500])
    print("\n" + "="*50 + "\n")
    
    # Try to parse as JSON
    data = json.loads(content)
    print(f"JSON parsed successfully! Found {len(data)} items")
    print("First item structure:")
    if data:
        print(json.dumps(data[0], indent=2))
        
except json.JSONDecodeError as e:
    print(f"JSON parsing error: {e}")
    print("This means the file is not valid JSON")
except Exception as e:
    print(f"Other error: {e}")