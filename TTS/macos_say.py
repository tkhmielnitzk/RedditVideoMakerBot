import random

import os
from typing import Final, Optional
from utils import settings

# say -v nom_de_la_voix "In Jojo Rabbit (2019), The movie never clarifies how she can fly or why her son Jojo is so distressed by this revelation."
# say -v "Good News" -r 200 "In Jojo Rabbit (2019), The movie never clarifies how she can fly or why her son Jojo is so distressed by this revelation."


eng_voices: Final[tuple] = (
    # "Agnes",
    # "Albert",
    # "Alex",
    # "Bad News", DROLE pas bon contexte
    # "Bahh",
    # "Bells", pas bon contexte trop lent
    # "Boing", pas bon contexte
    # "Bruce",
    # "Bubbles",
    # "Cellos", DROLE
    "Daniel",
    # "Deranged",
    # "Fred",
    # "Good News", DROLE pas bon contexte
    # "Hysterical",
    # "Junior",
    "Karen" # +++
    # "Kathy",
    # "Pipe Organ",
    # "Princess",
    # "Ralph",
    # "Samantha", 
    # "Trinoids",  pas bon contexte
    # "Vicki",
    # "Victoria",
    # "Whisper" pas bon contexte
    # "Zarvox" pas bon contexte
)

class MacOSsay:
    def __init__(self):
        self.max_chars = 5000
        self.voices = []

    def run(
        self,
        text: str,
        filepath: str,
        random_voice=False
    ):
        if random_voice:
            voice = self.randomvoice()
        else:
            voice = settings.config["settings"]["tts"]["python_voice"]

        
        self.use_say(text, filepath, voice)

    @staticmethod
    def randomvoice() -> str:
        return random.choice(eng_voices)

    def use_say(self, text, filepath, voice):
        """
        Use the macOS 'say' command, convert to MP3, and save.
        """

        escaped_text = text.replace('"', '\\"')
        temp_wav = "temp.aiff"  # Temporary file for the AIFF output

        say_command = f'say -v "{voice}" -r 160 -o "{temp_wav}" "{escaped_text}"'
        return_code = os.system(say_command)

        if return_code != 0:
            print(f"Error: 'say' command failed with return code {return_code}")
            return  # Or raise an exception

        # Convert to MP3 using lame
        mp3_filepath = filepath.replace(".aiff", ".mp3") # or ensure the filepath ends with .mp3
        lame_command = f'lame "{temp_wav}" "{mp3_filepath}"'  # Adjust lame quality if needed (-q 0 is best, -q 9 is worst)
        return_code = os.system(lame_command)

        if return_code != 0:
            print(f"Error: 'lame' command failed with return code {return_code}")
            os.remove(temp_wav) # Clean up the temp file
            return  # Or raise an exception

        os.remove(temp_wav)  # Clean up the temporary AIFF file
