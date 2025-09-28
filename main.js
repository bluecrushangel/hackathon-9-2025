// reqs:
// node 18+
// npm install node-fetch
// npm install dotenv
// package.json: { "type": "module" }

//how to run:
//have keys in a .env
///CLIENT_ID=<KEY>
///CLIENT_SECRET=<KEY>

import fetch from "node-fetch";
import fs from "fs";
import 'dotenv/config';

// Your Spotify app credentials (use env vars in production!)
const CLIENT_ID = process.env.SPOTIFY_CLIENT_ID;
const CLIENT_SECRET = process.env.SPOTIFY_CLIENT_SECRET;

// --- Helper: extract playlist ID from raw ID, URL, or spotify: URI ---
function extractPlaylistId(raw) {
  if (!raw) return null;
  const s = String(raw).trim();

  const urlMatch = s.match(/open\.spotify\.com\/playlist\/([A-Za-z0-9]+)(\?|$)/i);
  if (urlMatch) return urlMatch[1];

  const uriMatch = s.match(/spotify:playlist:([A-Za-z0-9]+)/i);
  if (uriMatch) return uriMatch[1];

  const idMatch = s.match(/^([A-Za-z0-9]{10,})$/);
  if (idMatch) return idMatch[1];

  return null;
}

// --- Get playlist id from argv or env ---
function getPlaylistId() {
  const fromArg = process.argv[2];
  const fromEnv = process.env.SPOTIFY_PLAYLIST_ID;
  const id = extractPlaylistId(fromArg) || extractPlaylistId(fromEnv);
  if (!id) {
    const msg =
`Usage:
  node main.js <playlistIdOrUrl>
  # or
  SPOTIFY_PLAYLIST_ID=<id> node main.js`;
    throw new Error(`No playlist ID provided.\n\n${msg}`);
  }
  return id;
}

// --- OAuth (Client Credentials) ---
async function getAccessToken() {
  const res = await fetch("https://accounts.spotify.com/api/token", {
    method: "POST",
    headers: {
      Authorization:
        "Basic " + Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64"),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: "grant_type=client_credentials",
  });
  if (!res.ok) throw new Error(`Token error: ${res.status} ${await res.text()}`);
  const json = await res.json();
  return json.access_token;
}

// --- Fetch ALL playlist tracks (handles pagination) ---
async function fetchAllPlaylistTracks(token, playlistId) {
  const items = [];
  let url = `https://api.spotify.com/v1/playlists/${playlistId}/tracks?limit=100`;
  while (url) {
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` }});
    if (!res.ok) throw new Error(`Playlist fetch error: ${res.status} ${await res.text()}`);
    const data = await res.json();
    items.push(...(data.items || []));
    url = data.next;
  }
  return items;
}

// --- Batch fetch artists (50 max per request) ---
async function fetchArtistsByIds(token, artistIds) {
  const unique = Array.from(new Set(artistIds));
  const result = new Map();

  for (let i = 0; i < unique.length; i += 50) {
    const batch = unique.slice(i, i + 50);
    const url = `https://api.spotify.com/v1/artists?ids=${batch.join(",")}`;
    const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` }});
    if (!res.ok) throw new Error(`Artists fetch error: ${res.status} ${await res.text()}`);
    const data = await res.json();
    for (const a of data.artists || []) result.set(a.id, a);
  }
  return result;
}

// --- Main: build JSON ---
(async () => {
  try {
    const PLAYLIST_ID = getPlaylistId();
    const token = await getAccessToken();
    const tracks = await fetchAllPlaylistTracks(token, PLAYLIST_ID);

    // Collect all artist IDs
    const artistIds = [];
    for (const it of tracks) {
      const track = it?.track;
      if (!track || track.type !== 'track') continue;
      for (const artist of track.artists || []) {
        if (artist?.id) artistIds.push(artist.id);
      }
    }

    const artistMap = await fetchArtistsByIds(token, artistIds);

    // Build structured JSON  
    const output = [];
    for (const it of tracks) {
      const track = it?.track;
      if (!track || track.type !== 'track') continue;

      const artistInfo = (track.artists || []).map((a) => {
        const full = artistMap.get(a.id);
        return {
          name: a.name,
          genres: full?.genres?.length ? full.genres : []
        };
      });

      output.push({
        track: track.name,
        artists: artistInfo
      });
    }

    // Save JSON file
    fs.writeFileSync("playlist_genres.json", JSON.stringify(output, null, 2));
    console.log(`✅ Saved ${output.length} tracks to playlist_genres.json`);

  } catch (err) {
    console.error(err.stack || err.message);
    process.exit(1);
  }
})();
