import random
import lyricsgenius
from dotenv import load_dotenv
import os
from typing import Final, List, Optional

load_dotenv()
GENIUS_API_TOKEN: Final[str] = os.getenv('GENIUS_TOKEN')

# Initialize LyricsGenius
genius = lyricsgenius.Genius(GENIUS_API_TOKEN)

def get_juice_wrld_songs():
    print("Fetching Juice WRLD songs...")
    artist = genius.search_artist("Juice WRLD", max_songs=20, sort="popularity")
    if artist and artist.songs:
        return artist.songs
    return []

def play_game():
    songs = get_juice_wrld_songs()
    if not songs:
        print("No Juice WRLD songs found.")
        return

    # Select a random song
    random_song = random.choice(songs)
    print(f"Selected Song: {random_song.title}\n")

    # Get the lyrics
    lyrics = random_song.lyrics
    if not lyrics:
        print(f"Could not fetch lyrics for {random_song.title}.")
        return

    # Select a random line
    lyrics_lines = [line for line in lyrics.split("\n") if line.strip()]
    if not lyrics_lines:
        print(f"No valid lyrics found for {random_song.title}.")
        return

    random_line = random.choice(lyrics_lines)
    print(f"Guess the Juice WRLD song from this line:\n")
    print(f"\"{random_line}\"\n")

    # Allow the player to guess
    user_guess = input("Your guess: ")
    if user_guess.lower() == random_song.title.lower():
        print(f"Correct! The song was \"{random_song.title}\".")
    else:
        print(f"Wrong. The correct answer was \"{random_song.title}\".")
        print(f"Listen to it here: {random_song.url}")

if __name__ == "__main__":
    play_game()