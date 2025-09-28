from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import google.generativeai as genai
from neo4j import GraphDatabase
import json
import os
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

app = FastAPI(title="Study Group Formation API")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Neo4j connection
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

# Pydantic models
class PlaylistInput(BaseModel):
    playlist_string: str

class PlaylistFileInput(BaseModel):
    file_path: str

class VibeResponse(BaseModel):
    user_display: Dict
    matching_results: Dict

# Buzzword templates for each category
BUZZWORD_TEMPLATES = {
    "deep_focus": [
        "Academic Dark Academia",
        "Mystical Library Vibes", 
        "Cosmic Study Sessions",
        "Ethereal Brain Food",
        "Zen Philosopher Mode",
        "Midnight Scholar Energy",
        "Dreamy Concentration Station",
        "Silent Genius Wavelength",
        "Monastic Study Ritual",
        "Deep Dive Intellect"
    ],
    
    "energetic_focus": [
        "Caffeinated Chaos Theory",
        "Electric Study Storm", 
        "Neon Productivity Surge",
        "Rocket Fuel Academia",
        "Lightning Brain Boost",
        "Turbocharged Knowledge",
        "High Voltage Learning",
        "Adrenaline Academic Rush",
        "Sonic Boom Study Mode",
        "Hyperactive Genius Energy"
    ],
    
    "balanced_focus": [
        "Golden Hour Study Club",
        "Cozy Coffee Shop Intellect",
        "Balanced Breakfast Brain",
        "Sunset Study Session",
        "Chill Academic Wanderer",
        "Easygoing Einstein Energy",
        "Versatile Vibe Scholar",
        "Autumn Leaf Learning",
        "Steady Stream Consciousness",
        "Harmonious Brain Waves"
    ],
    
    "intense_focus": [
        "Vampire Rage Football",
        "Nuclear Study Reactor",
        "Gladiator Brain Combat",
        "Tornado Intensity Mode",
        "Volcano Academic Fire",
        "Beast Mode Scholar",
        "Chaos Theory Mastery",
        "Savage Intellectual Warfare",
        "Apocalypse Study Survival",
        "Demon Mode Academia"
    ],
    
    "social_focus": [
        "Main Character Study Energy",
        "Golden Retriever Academia",
        "Sunshine Social Scholar",
        "Party Planning Genius",
        "Collaborative Butterfly Vibes",
        "Friendly Neighborhood Brain",
        "Group Project Superhero",
        "Extrovert Study Celebration",
        "Team Spirit Intelligence",
        "Social Butterfly Brilliance"
    ]
}

def get_vibe_emoji(category):
    """Get emoji for each vibe category"""
    emoji_map = {
        "deep_focus": "🧠✨📚",
        "energetic_focus": "⚡🚀💪", 
        "balanced_focus": "☀️☕📖",
        "intense_focus": "🔥💀⚔️",
        "social_focus": "🌟👥🎉"
    }
    return emoji_map.get(category, "🎵📚✨")

def get_personality_description(category):
    """Get personality description for each category"""
    descriptions = {
        "deep_focus": "You thrive in quiet, contemplative environments with complex material that requires sustained attention.",
        "energetic_focus": "You need high-energy, stimulating environments to maintain focus and tackle challenging work.",
        "balanced_focus": "You're adaptable and work well in various environments, bringing steady energy to any study session.",
        "intense_focus": "You excel under pressure and prefer complex, challenging material that pushes your limits.",
        "social_focus": "You learn best through collaboration and discussion, bringing positive energy to group settings."
    }
    return descriptions.get(category, "You have a unique study style!")

async def analyze_playlist_with_gemini(playlist_string: str) -> Dict:
    """Send playlist to Gemini for vibe analysis"""
    
    prompt = f"""
    Analyze this Spotify playlist and create a fun, quirky Spotify-style genre description using 2-4 random buzzwords.

    Playlist: {playlist_string}

    Examples of the style I want:
    - "Vampire Rage Football" (for aggressive rap/trap)
    - "Cottagecore Study Indie" (for soft indie folk)
    - "Neon Cyberpunk Vibes" (for electronic/synthwave)
    - "Melancholy Coffee Shop" (for sad indie/lo-fi)
    - "Cosmic Midnight Drive" (for dreamy electronic)
    - "Academic Dark Academia" (for classical/ambient)
    - "Chaotic Good Energy" (for eclectic mix)

    Create something unique and memorable that captures the vibe. Be creative with unexpected word combinations!

    Also categorize into one of these backend categories:
    - deep_focus: Ambient, instrumental, calming music for deep concentration
    - energetic_focus: Upbeat, rhythmic music for active studying  
    - balanced_focus: Diverse, moderate energy for flexible studying
    - intense_focus: Complex, challenging music for high-pressure studying
    - social_focus: Familiar, collaborative music for group studying

    Return ONLY valid JSON in this exact format:
    {{
        "spotify_vibe": "Your Creative Buzzword Combo",
        "backend_category": "deep_focus",
        "reasoning": "why this buzzword combo fits the music",
        "confidence": 0.85
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        
        # Clean the response text
        response_text = response.text.strip()
        
        # Remove any markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Validate the response has required fields
        required_fields = ["spotify_vibe", "backend_category", "reasoning", "confidence"]
        if not all(field in result for field in required_fields):
            raise ValueError("Missing required fields in Gemini response")
            
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw response: {response.text}")
        # Fallback response
        return {
            "spotify_vibe": random.choice(BUZZWORD_TEMPLATES["balanced_focus"]),
            "backend_category": "balanced_focus",
            "reasoning": "Fallback due to parsing error",
            "confidence": 0.5
        }
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Fallback response
        return {
            "spotify_vibe": random.choice(BUZZWORD_TEMPLATES["balanced_focus"]),
            "backend_category": "balanced_focus", 
            "reasoning": "Fallback due to API error",
            "confidence": 0.5
        }

def find_students_by_vibe(backend_category: str) -> List[Dict]:
    """Find students from Neo4j with matching vibe category"""
    
    with driver.session() as session:
        # First, let's check if students have studyVibe property
        result = session.run("""
            MATCH (s:Student)
            WHERE s.studyVibe = $category
            RETURN s.id as student_id, s.name as name, s.studyVibe as vibe,
                   s.learningStyle as learning_style, s.preferredPace as pace,
                   s.preferredCourseLoad as course_load
            LIMIT 20
        """, category=backend_category)
        
        students = []
        for record in result:
            students.append({
                "student_id": record["student_id"],
                "name": record["name"], 
                "vibe": record["vibe"],
                "learning_style": record["learning_style"],
                "pace": record["pace"],
                "course_load": record["course_load"]
            })
        
        # If no students found with studyVibe, assign vibes first
        if not students:
            print("No students found with studyVibe. Assigning vibes first...")
            assign_vibes_to_students()
            
            # Try again
            result = session.run("""
                MATCH (s:Student)
                WHERE s.studyVibe = $category
                RETURN s.id as student_id, s.name as name, s.studyVibe as vibe,
                       s.learningStyle as learning_style, s.preferredPace as pace,
                       s.preferredCourseLoad as course_load
                LIMIT 20
            """, category=backend_category)
            
            for record in result:
                students.append({
                    "student_id": record["student_id"],
                    "name": record["name"],
                    "vibe": record["vibe"],
                    "learning_style": record["learning_style"],
                    "pace": record["pace"],
                    "course_load": record["course_load"]
                })
        
        return students

def assign_vibes_to_students():
    """Assign study vibes to all students based on their characteristics"""
    
    with driver.session() as session:
        session.run("""
            MATCH (s:Student)
            SET s.studyVibe = CASE
                // Deep Focus: Visual/Reading-Writing + Slow/Moderate pace + Moderate/Heavy load
                WHEN s.learningStyle IN ['Visual', 'Reading-Writing'] 
                     AND s.preferredPace IN ['Slow', 'Moderate']
                     AND s.preferredCourseLoad IN ['Moderate', 'Heavy']
                THEN 'deep_focus'
                
                // Energetic Focus: Kinesthetic/Auditory + Fast pace
                WHEN s.learningStyle IN ['Kinesthetic', 'Auditory'] 
                     AND s.preferredPace = 'Fast'
                THEN 'energetic_focus'
                
                // Intense Focus: Heavy course load + Fast pace (any learning style)
                WHEN s.preferredCourseLoad = 'Heavy' 
                     AND s.preferredPace = 'Fast'
                THEN 'intense_focus'
                
                // Social Focus: Auditory/Kinesthetic + Light/Moderate load
                WHEN s.learningStyle IN ['Auditory', 'Kinesthetic']
                     AND s.preferredCourseLoad IN ['Light', 'Moderate']
                THEN 'social_focus'
                
                // Default: Balanced Focus
                ELSE 'balanced_focus'
            END
        """)
        print("Assigned study vibes to all students")

def form_study_groups(students: List[Dict], group_size: int = 4) -> List[Dict]:
    """Form study groups from matched students"""
    
    if len(students) < group_size:
        return [{
            "group_id": 1,
            "members": students,
            "group_analysis": {
                "size": len(students),
                "note": "Not enough students for full group, but here are your matches!"
            }
        }]
    
    groups = []
    for i in range(0, len(students), group_size):
        group_members = students[i:i+group_size]
        
        # Analyze group composition
        learning_styles = [s["learning_style"] for s in group_members]
        paces = [s["pace"] for s in group_members]
        course_loads = [s["course_load"] for s in group_members]
        
        group_analysis = {
            "group_size": len(group_members),
            "learning_style_diversity": len(set(learning_styles)),
            "pace_distribution": {pace: paces.count(pace) for pace in set(paces)},
            "course_load_distribution": {load: course_loads.count(load) for load in set(course_loads)},
            "compatibility_score": random.uniform(0.75, 0.95)  # Mock score for demo
        }
        
        groups.append({
            "group_id": len(groups) + 1,
            "members": group_members,
            "group_analysis": group_analysis
        })
    
    return groups

@app.get("/")
async def root():
    return {"message": "Study Group Formation API is running!"}

@app.post("/analyze-playlist", response_model=VibeResponse)
async def analyze_playlist(playlist_input: PlaylistInput):
    """Main endpoint: analyze playlist and return study group recommendations"""
    
    try:
        # Step 1: Analyze playlist with Gemini
        gemini_result = await analyze_playlist_with_gemini(playlist_input.playlist_string)
        
        # Step 2: Find matching students
        matching_students = find_students_by_vibe(gemini_result["backend_category"])
        
        # Step 3: Form study groups
        study_groups = form_study_groups(matching_students)
        
        # Step 4: Prepare response
        user_display = {
            "vibe_name": gemini_result["spotify_vibe"],
            "description": f"You're channeling {gemini_result['spotify_vibe']} energy!",
            "study_personality": get_personality_description(gemini_result["backend_category"]),
            "emoji": get_vibe_emoji(gemini_result["backend_category"]),
            "reasoning": gemini_result["reasoning"],
            "confidence": gemini_result["confidence"]
        }
        
        matching_results = {
            "backend_category": gemini_result["backend_category"],
            "total_matches": len(matching_students),
            "compatible_students": matching_students,
            "study_groups": study_groups,
            "success_message": f"Found {len(matching_students)} students who vibe with your {gemini_result['spotify_vibe']} energy!"
        }
        
        return VibeResponse(
            user_display=user_display,
            matching_results=matching_results
        )
        
    except Exception as e:
        print(f"Error in analyze_playlist: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/analyze-playlist-file", response_model=VibeResponse)
async def analyze_playlist_file(file_input: PlaylistFileInput):
    """Analyze playlist from a text file"""
    
    try:
        # Step 1: Read the file and convert to string
        playlist_string = read_playlist_file(file_input.file_path)
        
        # Step 2: Use the existing analysis function
        playlist_input = PlaylistInput(
            playlist_string=playlist_string,
            user_name=file_input.user_name
        )
        
        return await analyze_playlist(playlist_input)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_input.file_path}")
    except Exception as e:
        print(f"Error in analyze_playlist_file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

def read_playlist_file(file_path: str) -> str:
    """Read a text file and return its contents as a single string"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Clean up the content
        # Remove extra whitespace and newlines, but keep the text readable
        playlist_string = ' '.join(content.split())
        
        return playlist_string
        
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as file:
            content = file.read()
        
        playlist_string = ' '.join(content.split())
        return playlist_string

def read_playlist_json(file_path: str) -> str:
    """Read a JSON file and convert to playlist string format"""
    
    try:
        print(f"Attempting to read file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read and parse JSON
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"File content length: {len(content)} characters")
            
        # Parse JSON
        try:
            data = json.loads(content)
            print(f"JSON parsed successfully. Type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format: {str(e)}")
        
        # Validate data structure
        if not isinstance(data, list):
            raise Exception(f"Expected JSON array, got {type(data)}")
        
        if len(data) == 0:
            raise Exception("JSON file is empty")
        
        # Convert JSON to text format
        playlist_parts = []
        
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"Warning: Item {i} is not a dictionary, skipping")
                continue
                
            track_name = item.get('track', 'Unknown Track')
            artists = item.get('artists', [])
            
            if artists and isinstance(artists, list):
                for artist in artists:
                    if isinstance(artist, dict):
                        artist_name = artist.get('name', 'Unknown Artist')
                        genres = artist.get('genres', [])
                        
                        if genres and isinstance(genres, list):
                            genre_str = ', '.join(str(g) for g in genres)
                            playlist_parts.append(f"{track_name} by {artist_name} ({genre_str})")
                        else:
                            playlist_parts.append(f"{track_name} by {artist_name} (no genre data)")
            else:
                playlist_parts.append(f"{track_name} (no artist data)")
        
        result = '. '.join(playlist_parts)
        print(f"Converted to playlist string. Length: {len(result)} characters")
        
        if len(result) == 0:
            raise Exception("Converted playlist string is empty")
        
        return result
        
    except Exception as e:
        print(f"Error in read_playlist_json: {str(e)}")
        raise Exception(f"Error reading JSON file: {str(e)}")

@app.post("/analyze-playlist-json", response_model=VibeResponse)
async def analyze_playlist_json(file_input: PlaylistFileInput):
    """Analyze playlist from a JSON file (Spotify format)"""
    
    try:
        # Step 1: Read the JSON file and convert to string
        playlist_string = read_playlist_json(file_input.file_path)
        
        # Step 2: Use the existing analysis function
        playlist_input = PlaylistInput(playlist_string=playlist_string)
        
        return await analyze_playlist(playlist_input)
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {file_input.file_path}")
    except Exception as e:
        print(f"Error in analyze_playlist_json: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading JSON file: {str(e)}")

@app.post("/upload-playlist-file")
async def upload_playlist_file(file: UploadFile = File(...)):
    """Upload a playlist file and analyze it"""
    
    try:
        # Read the uploaded file
        content = await file.read()
        playlist_string = content.decode('utf-8')
        
        # Clean up the content
        playlist_string = ' '.join(playlist_string.split())
        
        # Analyze the playlist
        playlist_input = PlaylistInput(playlist_string=playlist_string)
        result = await analyze_playlist(playlist_input)
        
        return result
        
    except UnicodeDecodeError:
        try:
            # Try different encoding
            playlist_string = content.decode('latin-1')
            playlist_string = ' '.join(playlist_string.split())
            
            playlist_input = PlaylistInput(playlist_string=playlist_string)
            result = await analyze_playlist(playlist_input)
            return result
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not decode file: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/test-connection")
async def test_connection():
    """Test Neo4j connection"""
    try:
        with driver.session() as session:
            result = session.run("MATCH (s:Student) RETURN COUNT(s) as student_count")
            count = result.single()["student_count"]
            return {"status": "connected", "student_count": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/vibe-distribution")
async def get_vibe_distribution():
    """Get distribution of study vibes in the database"""
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (s:Student)
                RETURN s.studyVibe as vibe, COUNT(s) as count
                ORDER BY count DESC
            """)
            
            distribution = []
            for record in result:
                distribution.append({
                    "vibe": record["vibe"],
                    "count": record["count"]
                })
            
            return {"vibe_distribution": distribution}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)