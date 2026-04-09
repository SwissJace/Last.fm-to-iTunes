import pylast
import win32com.client
from thefuzz import fuzz
from collections import Counter
import time

API_KEY = "YOUR API KEY"
API_SECRET = "YOUR API SECRET"
USER_NAME = "YOUR USERNAME"
CONFIDENCE_THRESHOLD = 50 
# THE THRESHOLD IS THE CONFIDENCE IN WHICH IT WILL MATCH THE SCROBBLES TO YOUR LOCAL LIBRARY. 

network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)
user = network.get_user(USER_NAME)

def get_all_scrobbles():
    print(f"Fetching full history for {USER_NAME}...")
    all_scrobbles = []
    
    try:
        tracks_generator = user.get_recent_tracks(limit=None, stream=True)
        
        count = 0
        for ts in tracks_generator:
            artist = ts.track.artist.name
            title = ts.track.title
            all_scrobbles.append(f"{artist} - {title}")
            
            count += 1
            if count % 100 == 0:
                print(f"Retrieved {count} scrobbles...")
                
    except Exception as e:
        print(f"An error occurred: {e}")
            
    return Counter(all_scrobbles)

def sync_to_itunes(scrobble_counts):
    print("\nConnecting to iTunes...")
    itunes = win32com.client.Dispatch("iTunes.Application")
    library = itunes.LibraryPlaylist
    
    total_tracks = len(scrobble_counts)
    current = 0

    for track_info, count in scrobble_counts.items():
        current += 1
        artist_name, track_name = track_info.split(" - ", 1)
        print(f"[{current}/{total_tracks}] Processing: {artist_name} - {track_name} ({count} plays)")

        search_results = library.Search(artist_name, 0)
        
        best_match = None
        highest_score = 0

        if search_results:
            for i in range(1, search_results.Count + 1):
                it_track = search_results.Item(i)
                it_full_string = f"{it_track.Artist} {it_track.Name}".lower()
                
                # Fuzzy comparison
                score = fuzz.token_set_ratio(track_info.lower(), it_full_string)
                
                if score > highest_score:
                    highest_score = score
                    best_match = it_track
                  
        if best_match and highest_score >= CONFIDENCE_THRESHOLD:
            best_match.PlayedCount += count
            print(f"   Successfully matched ({highest_score}%)! Added {count} plays.")
        else:
            print(f"   No match found for {track_info}")

if __name__ == "__main__":
    counts = get_all_scrobbles()
    
    if counts:
        sync_to_itunes(counts)
        print("\nFull history sync complete!")
