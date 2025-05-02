import lyricsgenius
from dotenv import load_dotenv
import os
from typing import Final

load_dotenv()
GENIUS_API_TOKEN: Final[str] = os.getenv('GENIUS_TOKEN')

genius = lyricsgenius.Genius(GENIUS_API_TOKEN)

while 1==1:
    song_name = input("Enter the song name: ")

    song = genius.search_song(song_name)
    if song:
        print(song.lyrics)
    else:
        print("Song not found!")


