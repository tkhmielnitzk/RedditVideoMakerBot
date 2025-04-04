import random
import os
from typing import Final
from utils import settings

eng_voices: Final[tuple] = (
    # "en-us+f1",  # Female voice 1
    # "en-us+f2",  # Female voice 2
    # "en-us+m1",  # Male voice 1
    # "en-us+m2",  # Male voice 2
    # "en-us+m3",  # Male voice 3
    "en",
    "en-us"
)

class LinuxEspeak:
    def __init__(self):
        self.max_chars = 5000
        self.voices = eng_voices

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

        self.use_espeak(text, filepath, voice)

    @staticmethod
    def randomvoice() -> str:
        to_return = random.choice(eng_voices)
        print(f"Using voice: {to_return}")
        return to_return

    def use_espeak(self, text, filepath, voice):
        """
        Use 'espeak' to generate a WAV file, then convert it to MP3 using ffmpeg.
        """
        escaped_text = text.replace('"', '\\"')
        temp_wav = "temp.wav"

        # Generate speech with espeak
        espeak_command = f'espeak-ng -v {voice} -s 160 -w "{temp_wav}" "{escaped_text}"'
        return_code = os.system(espeak_command)

        if return_code != 0:
            print(f"Error: 'espeak' command failed with return code {return_code}")
            return

        # Convert WAV to MP3 using ffmpeg
        mp3_filepath = filepath.replace(".wav", ".mp3")
        ffmpeg_command = f'ffmpeg -i "{temp_wav}" -codec:a libmp3lame -qscale:a 2 "{mp3_filepath}" -y'
        return_code = os.system(ffmpeg_command)

        if return_code != 0:
            print(f"Error: 'ffmpeg' command failed with return code {return_code}")
            os.remove(temp_wav)
            return

        os.remove(temp_wav)  # Clean up temporary WAV file