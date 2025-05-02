import random

# Define the file path
file_path = "songs.txt"

def get_all_songs(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
        
        songs = [line.strip() for line in lines if line.strip()]
        
        if not songs:
            return "No songs available in the file."
        
        formatted_songs = "\n".join([f"{index + 1}. {song}" for index, song in enumerate(songs)])
        return formatted_songs
    
    except FileNotFoundError:
        return f"File '{file_path}' not found."
    
    except Exception as e:
        return f"An error occurred: {e}"


#print(get_all_songs(file_path))


def get_random_song(file_path):
    try:
        # Open the file and read all lines
        with open(file_path, "r") as file:
            lines = file.readlines()
        
        # Remove newline characters and empty lines
        songs = [line.strip() for line in lines if line.strip()]
        
        # If there are no songs, return a message
        if not songs:
            return "No songs available in the file."

        # Return a random song from the list
        return random.choice(songs)
    
    except FileNotFoundError:
        return f"File '{file_path}' not found."
    
    except Exception as e:
        return f"An error occurred: {e}"

# Call the function and print the result
#print(get_random_song(file_path))