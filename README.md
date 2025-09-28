🎵 Spotify Playlist Genre Extractor

A Node.js script that fetches tracks from a Spotify playlist and saves their artists + genres into a clean JSON file. Useful for hackathons, music analysis projects, or just exploring what kinds of genres your playlists contain.

🚀 Features

Fetches all tracks from any public Spotify playlist

Collects each artist’s genres (if available)

Saves results into a playlist_genres.json file

Handles pagination automatically (works with playlists of any size)

Securely uses API keys via .env

🛠️ Requirements

Node.js 18+

npm (comes with Node)

A Spotify Developer App
 to get a Client ID and Client Secret

📦 Installation

Clone the repo

git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>


Install dependencies

npm install


Set up environment variables
Create a .env file in the project root:

SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret


⚠️ Add .env to .gitignore so you don’t commit secrets:

echo ".env" >> .gitignore

▶️ Usage

Run the script with a playlist URL or ID:

node main.js https://open.spotify.com/playlist/55YzdwbNLu58KdYhMW5ANf


or

SPOTIFY_PLAYLIST_ID=55YzdwbNLu58KdYhMW5ANf node main.js

📂 Output

After running, you’ll get a file:

playlist_genres.json

[
  {
    "track": "Blinding Lights",
    "artists": [
      {
        "name": "The Weeknd",
        "genres": ["canadian contemporary r&b", "pop", "urban contemporary"]
      }
    ]
  },
  {
    "track": "Unknown Collab",
    "artists": [
      {
        "name": "Indie Artist",
        "genres": ["indie pop", "bedroom pop"]
      },
      {
        "name": "Newcomer X",
        "genres": []
      }
    ]
  }
]

⚠️ Notes

Works only with public playlists. Private playlists require the Authorization Code flow (user login).

If an artist has no genres available from Spotify, they will be listed with "genres": [].

Large playlists are automatically paginated (100 tracks per page).

📄 License

MIT — free to use, modify, and share.