import requests
import os
from dotenv import load_dotenv
from typing import Final, List, Optional

load_dotenv()
API_TOKEN: Final[str] = os.getenv('GENIUS_TOKEN')
BASE_URL = "https://api.genius.com"

def search_juice_wrld_songs_by_lyrics(lyrics_snippet):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }
    params = {
        "q": lyrics_snippet  # The lyrics snippet to search
    }
    
    response = requests.get(f"{BASE_URL}/search", headers=headers, params=params)
    
    if response.status_code == 200:
        results = response.json()["response"]["hits"]
        
        # Filter for Juice WRLD songs
        juice_wrld_songs = [
            hit["result"] for hit in results
            if "Juice WRLD" in hit["result"]["primary_artist"]["name"]
        ]
        
        if juice_wrld_songs:
            print("\nMatching Juice WRLD songs:")
            for song in juice_wrld_songs:
                print(f"Title: {song['title']}")
                print(f"Artist: {song['primary_artist']['name']}")
                print(f"URL: {song['url']}\n")
            return juice_wrld_songs
        else:
            print("No Juice WRLD songs found with those lyrics.")



        xxxtentacion_songs = [
                hit["result"] for hit in results
                if "XXXTENTACION" in hit["result"]["primary_artist"]["name"]
            ]
            
        if xxxtentacion_songs:
            print("\nMatching XXXTENTACION songs:")
            for song in xxxtentacion_songs:
                print(f"Title: {song['title']}")
                print(f"Artist: {song['primary_artist']['name']}")
                print(f"URL: {song['url']}\n")
            return xxxtentacion_songs
        else:
            print("No XXXTENTACION songs found with those lyrics.")
        
    else:
        print(f"Error: {response.status_code}, {response.text}")

if __name__ == "__main__":
    lyrics_snippet = input("Enter a lyrics snippet: ")
    search_juice_wrld_songs_by_lyrics(lyrics_snippet)
