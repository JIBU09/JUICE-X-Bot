from typing import Final, List, Optional
import os
from dotenv import load_dotenv
import discord
from discord import Intents, Interaction, VoiceChannel, FFmpegPCMAudio, Embed, ButtonStyle, File
from discord.ext import commands, tasks
from discord.ui import Button, View
import yt_dlp
import asyncio
from datetime import datetime
import random
import difflib
from bs4 import BeautifulSoup
import aiohttp
import lyricsgenius
import requests
import pytz

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
GENIUS_API_TOKEN: Final[str] = os.getenv('GENIUS_TOKEN')
genius = lyricsgenius.Genius(GENIUS_API_TOKEN)
BASE_URL = "https://api.genius.com"
file_path = "songs.txt"
BASE_PATH = "bot"
SONG_LYRICS_PATH = os.path.join("SongLyrics")
IMAGE_PATH = os.path.join("images")
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}


intents: Intents = Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="?", intents=intents)


#Emojis
siren = '<a:Siren:1296021211863842816>'
musicDisc = '<a:musiccdspin:1296020609364394035>'


# Music player class
class MusicPlayer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.queue: List[str] = []
        self.is_playing = False
        self.vc: Optional[discord.VoiceClient] = None

    async def join_voice_channel(self):
        if not self.ctx.user.voice:

            #-----------------------------------
            embed = discord.Embed(
                colour=discord.Colour.red(),
                title=f"{siren} Can't join",
                description="You're not connected to a voice channel!"
            )
            message = await self.ctx.followup.send(embed=embed)
            await message.delete(delay=5)
            #-----------------------------------

            return False

        voice_channel = self.ctx.user.voice.channel

        if self.ctx.guild.voice_client is None:
            self.vc = await voice_channel.connect()
        elif self.ctx.guild.voice_client.is_connected():
            await self.ctx.guild.voice_client.move_to(voice_channel)

        return True

    async def play_next(self):
        if self.queue:
            self.is_playing = True
            url = self.queue.pop(0)

            # Download the audio with yt-dlp
            with yt_dlp.YoutubeDL({'format': 'bestaudio'}) as ydl:
                info = ydl.extract_info(url, download=False)
                url2 = info['url']
                source = discord.FFmpegPCMAudio(url2, **FFMPEG_OPTIONS)

                # Play the audio
                self.vc.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), bot.loop))

                # Create the control buttons view
                view = MusicControlView()  

                # Create the embed for the currently playing song
                embed = discord.Embed(
                    colour=discord.Colour.dark_gray(),
                    title=f"{musicDisc} {info['title']}",
                    description=f"[{info['title']}]({url}) is now playing",
                )
                embed.set_thumbnail(url=info.get('thumbnail', ''))

                # Send the embed message
                await self.ctx.followup.send(embed=embed, view=view)

        else:
            self.is_playing = False




    async def add_to_queue(self, query):
        # Search for the song by name using yt-dlp
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': 'True'}) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
                url = info['webpage_url']
                thumbnail = info['thumbnail']  # Extract the thumbnail URL
                self.queue.append(url)
                if not self.is_playing:
                    await self.play_next()
                return info['title'], url, thumbnail  # Return title, URL, and thumbnail
            except Exception as e:
                print(f"An error occurred while searching for the song: {e}")
                return None, None, None


    async def stop(self):
        if self.vc:
            await self.vc.disconnect()

music_player = None

# Startup
@bot.event
async def on_ready() -> None:    
    print(f'{bot.user} is now running!')

    with open('patchValue.txt', 'r') as file:
        line = file.read().strip()
    value = int(line.split('=')[1].strip())
    #value += 1
    new_line = f'patch = {value}'
    with open('patchValue.txt', 'w') as file:
        file.write(new_line)


    timezone = pytz.timezone('Europe/Berlin')
    current_time = datetime.now(timezone).time()
    current_date = datetime.now(timezone).date()
    
    print(f"Running on Patch {value} [{current_time}, {current_date}]")

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="JUICE & X"))
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as e:
        print(f"An error occurred when syncing commands: {e}")

# Button UI for controlling the player (with Pause/Resume toggle)
class MusicControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="◼ Stop", style=discord.ButtonStyle.danger)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global music_player
        if music_player:
            await music_player.stop()
            music_player = None

            user = interaction.user
            user_avatar_url = user.display_avatar.url

            embed = discord.Embed(
                colour=discord.Colour.dark_gray(),
                title=f"Music Stopped",
                description=f"{user.mention} requested to stopped the music and to clear the queue."
            )
        
            embed.set_thumbnail(url=user_avatar_url)

            # Defer the interaction to prevent timeout
            await interaction.response.defer()

            # Send the follow-up message and delete after 10 seconds
            message = await interaction.followup.send(embed=embed)
            await message.delete(delay=10)

        else:
            embed = discord.Embed(
                colour=discord.Colour.red(),
                title=f"{siren} No Music",
                description="No music is playing."
            )

            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)
            await message.delete(delay=5)


    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.primary)
    async def toggle_pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            button.label = "Resume"


            user = interaction.user
            user_avatar_url = user.display_avatar.url  # Get user's profile picture

            # Create the embed with the user's avatar and name
            embed = discord.Embed(
                colour=discord.Colour.dark_gray(),
                title="Music Paused",
                description=f"{user.mention} paused the music."
            )

            # Set the thumbnail to the user's profile picture
            embed.set_thumbnail(url=user_avatar_url)

            # Defer the interaction and send the embed
            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)
        
            # Delete the message after 10 seconds
            await message.delete(delay=10)


        elif vc and vc.is_paused():
            vc.resume()
            button.label = "Pause"

            user = interaction.user
            user_avatar_url = user.display_avatar.url

            embed = discord.Embed(
                colour=discord.Colour.dark_gray(),
                title="Music Resumed",
                description=f"{user.mention} resumed the music."
            )

            embed.set_thumbnail(url=user_avatar_url)

            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)

            await message.delete(delay=10)

        else:
            embed = discord.Embed(
                colour=discord.Colour.red(),
                title=f"{siren} No Music",
                description="No music is playing."
            )
            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)
            await message.delete(delay=5)

    @discord.ui.button(label=f"Skip", style=discord.ButtonStyle.success)
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()

            user = interaction.user
            user_avatar_url = user.display_avatar.url

            embed = discord.Embed(
                colour=discord.Colour.dark_gray(),
                title="Song Skipped",
                description=f"{user.mention} skipped the song."
            )

            embed.set_thumbnail(url=user_avatar_url)

            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)

            await message.delete(delay=10)
        else:
            embed = discord.Embed(
                colour=discord.Colour.red(),
                title=f"{siren} No Music",
                description="No music is playing."
            )
            await interaction.response.defer()
            message = await interaction.followup.send(embed=embed)
            await message.delete(delay=5)


# Play Command with Control Buttons and Search by Name
@bot.tree.command(name="play", description="Plays a song by searching for the name")
async def play(interaction: discord.Interaction, query: str):
    global music_player
    if music_player is None:
        music_player = MusicPlayer(interaction)

    try:
        await interaction.response.defer()

        # Attempt to join voice channel
        if await music_player.join_voice_channel():
            user = interaction.user
            title, url, thumbnail = await music_player.add_to_queue(query)
            if title and url:
                embed = discord.Embed(
                    colour=discord.Colour.dark_gray(),
                    title=f"{title}",
                    description=f"[{title}]({url}) was added to the queue by {user.mention}",
                )
                embed.set_thumbnail(url=thumbnail)
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    colour=discord.Colour.red(),
                    title=f"{siren} Song not found",
                    description="The song you requested could not be found."
                )
                message = await interaction.followup.send(embed=embed)
                await message.delete(delay=10)
    except Exception as e:
        await interaction.followup.send(f"An error occurred. Please contact <@{699539532621545563}>.")
        await bot.get_channel(1291823150140624989).send(f"An error occurred: {e}")

# Pause Command
@bot.tree.command(name="pause", description="Pauses the current song")
async def pause(interaction: Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        user = interaction.user
        user_avatar_url = user.display_avatar.url

        embed = discord.Embed(
            colour=discord.Colour.dark_gray(),
            title="Music Paused",
            description=f"{user.mention} paused the music."
        )

        embed.set_thumbnail(url=user_avatar_url)

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)

        await message.delete(delay=10)

    else:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=f"{siren} No Music",
            description="No music is playing."
        )
        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        await message.delete(delay=5)

# Resume Command
@bot.tree.command(name="resume", description="Resumes the current song")
async def resume(interaction: Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        user = interaction.user
        user_avatar_url = user.display_avatar.url

        embed = discord.Embed(
            colour=discord.Colour.dark_gray(),
            title="Music Resumed",
            description=f"{user.mention} resumed the music."
        )

        embed.set_thumbnail(url=user_avatar_url)

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)

        await message.delete(delay=10)

    else:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=f"{siren} Music Playing",
            description="The music is already playing."
        )
        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        await message.delete(delay=5)

# Skip Command
@bot.tree.command(name="skip", description="Skips the current song")
async def skip(interaction: Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        user = interaction.user
        user_avatar_url = user.display_avatar.url

        embed = discord.Embed(
            colour=discord.Colour.dark_gray(),
            title=f"Song Skipped",
            description=f"{user.mention} skipped the previous song."
        )

        embed.set_thumbnail(url=user_avatar_url)

        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)

        await message.delete(delay=20)
    else:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=f"{siren} No Music",
            description="No music is playing."
        )
        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        await message.delete(delay=5)

# Stop Command
@bot.tree.command(name="stop", description="Stops the music and clears the queue")
async def stop(interaction: Interaction):
    global music_player
    if music_player:
        await music_player.stop()
        music_player = None
        user = interaction.user
        user_avatar_url = user.display_avatar.url

        embed = discord.Embed(
            colour=discord.Colour.dark_gray(),
            title=f"Music Stopped",
            description=f"{user.mention} requested to stopped the music and to clear the queue."
        )
        
        embed.set_thumbnail(url=user_avatar_url)

        await interaction.response.defer()

        message = await interaction.followup.send(embed=embed)
        await message.delete(delay=10)
    else:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=f"{siren} No Music",
            description="No music is playing."
        )
        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed)
        await message.delete(delay=5)


@bot.tree.command(name="queue", description="Shows the current song queue")
async def show_queue(interaction: discord.Interaction):
    global music_player
    if music_player is None or not music_player.queue:
        embed = discord.Embed(
            colour=discord.Colour.red(),
            title=f"{siren} Empty Queue",
            description="The Queue is currently empty."
        )
        await interaction.response.defer()
        message = await interaction.followup.send(embed=embed, ephemeral=True)
        await message.delete(delay=5)
    else:
        queue_list = "\n".join([f"{index + 1}. {url}" for index, url in enumerate(music_player.queue)])
        await interaction.response.send_message(f"**Current Queue:**\n{queue_list}", ephemeral=True)


@bot.event
async def on_member_join(member):
    try:
        channel = bot.get_channel(1288893546312634418)
        user_avatar_url = member.display_avatar.url
        
        embed = discord.Embed(
            description=f"**{member.mention}** ended up in Copper too.",
            colour=discord.Colour.dark_gray(),
        )
        embed.set_thumbnail(url=user_avatar_url)
        
        role = discord.utils.get(member.guild.roles, name="ONLINE")
        
        if role:
            await member.add_roles(role)
        
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Error: {e}")









@bot.tree.command(name="guess_songs", description="Guess the song by XXXTENTACION or Juice WRLD")
async def guess_songs(interaction: discord.Interaction, artist: Optional[str] = None, difficulty: Optional[str] = None, rounds: Optional[int] = 5):
    artist_choices = ["XXXTENTACION", "JuiceWRLD"]
    difficulty_choices = ["Easy", "Medium", "Hard", "Extreme"]

    # Handle case-insensitivity and automatic artist selection
    if artist:
        artist = artist.lower()
        if 'x' in artist:
            artist = "XXXTENTACION"
        elif 'j' in artist:
            artist = "JuiceWRLD"
    else:
        artist = random.choice(artist_choices)

    if difficulty:
        difficulty = difficulty.capitalize()
    else:
        difficulty = random.choice(difficulty_choices)

    if artist not in artist_choices or difficulty not in difficulty_choices:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Invalid input! Artist must be one of {', '.join(artist_choices)}, and difficulty must be one of {', '.join(difficulty_choices)}.",
                color=discord.Color.red()
            )
        )
        return

    artist_path = os.path.join(SONG_LYRICS_PATH, artist, difficulty)
    if not os.path.exists(artist_path):
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"No songs found for {artist} at {difficulty} difficulty.",
                color=discord.Color.red()
            )
        )
        return

    song_files = [f for f in os.listdir(artist_path) if f.endswith(".txt")]
    if not song_files:
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"No songs found for {artist} at {difficulty} difficulty.",
                color=discord.Color.red()
            )
        )
        return

    rounds = min(rounds, len(song_files))
    selected_songs = random.sample(song_files, rounds)

    async def game_round(song, options):
        song_path = os.path.join(artist_path, song)
        with open(song_path, "r") as file:
            lyrics = file.read()

        song_name = song.replace(".txt", "")
        lines = [line for line in lyrics.splitlines() if len(line) >= 10]
        if not lines:
            return

        random_line = random.choice(lines)
        clue = random_line[:50]

        embed = discord.Embed(
            title="Guess the Song!",
            description=f"Clue: {clue}\n\n**Song options:** {', '.join(options)}",
            color=discord.Color.blue()
        )

        view = discord.ui.View()

        correct_song_added = False

        for option in options:
            button = discord.ui.Button(
                label=option,
                style=discord.ButtonStyle.primary
            )

            async def button_callback(interaction: discord.Interaction, chosen=option):
                nonlocal correct_song_added
                if chosen == song_name:
                    response = discord.Embed(
                        description=f"Correct! 🎉 The song was: {song_name}",
                        color=discord.Color.green()
                    )
                    if interaction.user.voice and music_player and music_player.is_playing:
                        await music_player.add_to_queue(f"{song_name} - {artist}")
                        correct_song_added = True
                else:
                    response = discord.Embed(
                        description=f"Incorrect! 😢 The song was: {song_name}",
                        color=discord.Color.red()
                    )
                await interaction.response.edit_message(embed=response, view=None)

            button.callback = button_callback
            view.add_item(button)

        await interaction.followup.send(embed=embed, view=view)

        while not correct_song_added:
            await asyncio.sleep(0.5)  # Wait for the user to respond correctly

    await interaction.response.defer()

    for song in selected_songs:
        options = random.sample(song_files, k=5)
        options = [opt.replace(".txt", "") for opt in options]
        if song.replace(".txt", "") not in options:
            options[random.randint(0, 4)] = song.replace(".txt", "")
        random.shuffle(options)
        await game_round(song, options)




@bot.tree.command(name="song_pool", description="View all available songs for a specific artist and/or difficulty.")
async def song_pool(interaction: discord.Interaction, artist: Optional[str] = None, difficulty: Optional[str] = None):
    artist_choices = ["XXXTENTACION", "JuiceWRLD"]
    difficulty_choices = ["Easy", "Medium", "Hard", "Extreme"]
    
    # If no artist is specified, use both artists
    if artist and artist not in artist_choices:
        await interaction.response.send_message(embed=discord.Embed(
            description=f"Invalid artist! Choose from {', '.join(artist_choices)}.", 
            color=discord.Color.red()))
        return

    # If no difficulty is specified, use all difficulties
    if difficulty and difficulty not in difficulty_choices:
        await interaction.response.send_message(embed=discord.Embed(
            description=f"Invalid difficulty! Choose from {', '.join(difficulty_choices)}.", 
            color=discord.Color.red()))
        return

    # Prepare to list songs for the given artist and difficulty
    if artist and difficulty:
        artist_path = os.path.join(SONG_LYRICS_PATH, artist, difficulty)
    elif artist:
        artist_path = os.path.join(SONG_LYRICS_PATH, artist)
    elif difficulty:
        artist_path = os.path.join(SONG_LYRICS_PATH, difficulty)
    else:
        artist_path = SONG_LYRICS_PATH  # Default to the root directory if no filters

    # Print the path to the console for debugging
    print(f"Looking for songs in: {artist_path}")
    
    if not os.path.exists(artist_path):
        await interaction.response.send_message(embed=discord.Embed(
            description=f"No songs found for {artist if artist else 'any artist'} with {difficulty if difficulty else 'any difficulty'}.", 
            color=discord.Color.red()))
        return

    song_files = [f for f in os.listdir(artist_path) if f.endswith(".txt")]
    
    # Print all found song files for debugging
    print(f"Found the following song files: {song_files}")
    
    if not song_files:
        await interaction.response.send_message(embed=discord.Embed(
            description=f"No songs found for {artist if artist else 'any artist'} with {difficulty if difficulty else 'any difficulty'}.", 
            color=discord.Color.red()))
        return

    # Create a list of available songs
    song_list = "\n".join([song.replace(".txt", "") for song in song_files])

    # Send the list of songs as a message
    embed = discord.Embed(
        title="Available Songs",
        description=f"Here are the songs available for {artist if artist else 'any artist'} and {difficulty if difficulty else 'any difficulty'}:\n\n{song_list}",
        color=discord.Color.blue())
    
    await interaction.response.send_message(embed=embed)





@bot.tree.command(name="get_song", description="Find a song by JuiceWRLD or XXXTENTACION by providing a lyric snippet.")
async def get_song(interaction: discord.Interaction, lyric_snippet: str):
    await interaction.response.defer()

    matching_songs = []
    similar_songs = []

    # Go through all songs and check for the lyric snippet
    for artist in os.listdir(SONG_LYRICS_PATH):
        artist_path = os.path.join(SONG_LYRICS_PATH, artist)
        if not os.path.isdir(artist_path):
            continue

        for difficulty in os.listdir(artist_path):
            difficulty_path = os.path.join(artist_path, difficulty)
            if not os.path.isdir(difficulty_path):
                continue

            for song_file in os.listdir(difficulty_path):
                if not song_file.endswith(".txt"):
                    continue

                song_path = os.path.join(difficulty_path, song_file)
                with open(song_path, "r") as file:
                    lyrics = file.read()
                    song_name = song_file.replace(".txt", "")

                    # Check for an exact match
                    if lyric_snippet.lower() in lyrics.lower():
                        matching_songs.append(f"{song_name} by {artist} [{difficulty}]")
                        continue  # Skip checking for similarity if exact match is found

                    # Check for similar lyrics
                    for line in lyrics.splitlines():
                        similarity = difflib.SequenceMatcher(None, lyric_snippet.lower(), line.lower()).ratio()
                        if similarity > 0.7:
                            similar_songs.append(f"{song_name} by {artist} [{difficulty}]")
                            break  # Avoid adding the same song multiple times for similar lines

    # Remove duplicates in case of multiple matches
    matching_songs = list(set(matching_songs))
    similar_songs = list(set(similar_songs))

    # Prepare response
    if matching_songs:
        embed = discord.Embed(
            title="Matching Songs",
            description="The following songs contain the exact lyric snippet:\n" +
                        "\n".join(matching_songs),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
    elif similar_songs:
        embed = discord.Embed(
            title="Similar Songs",
            description="No exact matches found, but these songs have similar lyrics:\n" +
                        "\n".join(similar_songs),
            color=discord.Color.orange()
        )
        await interaction.followup.send(embed=embed)
    else:
        # Trigger Genius API search for Juice WRLD and XXXTENTACION songs
        juice_wrld_songs, xxxtentacion_songs = search_songs_by_lyrics(lyric_snippet)

        if juice_wrld_songs or xxxtentacion_songs:
            embed = discord.Embed(
                title="Search Results",
                description="No local matches found, but these songs might match your snippet:",
                color=discord.Color.purple()
            )
            if juice_wrld_songs:
                embed.add_field(
                    name="Juice WRLD Songs",
                    value="\n".join(
                        f"[{song['title']}]({song['url']}) by {song['primary_artist']['name']}" 
                        for song in juice_wrld_songs
                    ),
                    inline=False
                )
            if xxxtentacion_songs:
                embed.add_field(
                    name="XXXTENTACION Songs",
                    value="\n".join(
                        f"[{song['title']}]({song['url']}) by {song['primary_artist']['name']}" 
                        for song in xxxtentacion_songs
                    ),
                    inline=False
                )
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="No Songs Found",
                description="No songs contain the provided lyric snippet, and no similar matches were found.",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)


def search_songs_by_lyrics(lyrics_snippet):
    headers = {
        "Authorization": f"Bearer {GENIUS_API_TOKEN}"
    }
    params = {
        "q": lyrics_snippet
    }
    
    response = requests.get(f"{BASE_URL}/search", headers=headers, params=params)
    
    if response.status_code == 200:
        results = response.json()["response"]["hits"]
        
        # Filter for Juice WRLD songs
        juice_wrld_songs = [
            hit["result"] for hit in results
            if "Juice WRLD" in hit["result"]["primary_artist"]["name"]
        ]

        # Filter for XXXTENTACION songs
        xxxtentacion_songs = [
            hit["result"] for hit in results
            if "XXXTENTACION" in hit["result"]["primary_artist"]["name"]
        ]
        
        return juice_wrld_songs, xxxtentacion_songs
    else:
        return [], []
    



@bot.tree.command(name="get_lyrics", description="Get lyrics of any song.")
async def get_song(interaction: discord.Interaction, song_name: str):
    await interaction.response.defer()  # Prevent timeout during processing
    lyrics = getLyrics(song_name)
    
    if not lyrics:
        embed = discord.Embed(
            title="Could not find the lyrics",
            description="The lyrics could not be found!",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)
    else:
        chunks = [lyrics[i:i+4096] for i in range(0, len(lyrics), 4096)]
        embeds = []
        
        for idx, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"Lyrics for {song_name}" if idx == 0 else f"Lyrics (continued) - Part {idx+1}",
                description=chunk,
                color=discord.Color.blue()
            )
            embeds.append(embed)

        # Send each embed in sequence
        for embed in embeds:
            await interaction.followup.send(embed=embed)

        print("Lyrics successfully sent!")



def getLyrics(song_name):
    # Ruft Lyrics über die Genius-API ab
    try:
        song = genius.search_song(song_name)
        if song:
            print(f"Song gefunden: {song.title}")
            return song.lyrics
        else:
            print("Song nicht gefunden.")
            return None
    except Exception as e:
        print(f"Fehler bei der Lyrics-Suche: {e}")
        return None

# Run the bot
async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())
