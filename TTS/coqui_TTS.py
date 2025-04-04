import random
import os
from typing import Final
from TTS.utils.synthesizer import Synthesizer
from utils import settings

# Pre-defined voices (You can modify this as needed for your voices)
eng_voices: Final[tuple] = (
    "en",        # English voice
    "en-us",      # English US voice
)

class LinuxTTS:
    def __init__(self):
        # Model paths for Coqui-TTS (You need to set these to actual model paths on your system)
        self.model_path = "path/to/your/model.pth"  # Change this to your model path
        self.config_path = "path/to/your/config.json"  # Change this to your config path
        self.vocoder_model_path = "path/to/your/vocoder_model.pth"  # Optional for vocoder model (HiFi-GAN)
        self.max_chars = 5000
        self.voices = eng_voices

        # Initialize TTS synthesizer
        self.synthesizer = Synthesizer(
            tts_checkpoint=self.model_path,
            tts_config_path=self.config_path,
            vocoder_checkpoint=self.vocoder_model_path,
            vocoder_config_path=self.config_path,
            use_cuda=False  # Set to True if you have a GPU and want to use it
        )

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

        self.use_coqui_tts(text, filepath, voice)

    @staticmethod
    def randomvoice() -> str:
        """Randomly select a voice from the available options."""
        to_return = random.choice(eng_voices)
        print(f"Using voice: {to_return}")
        return to_return

    def use_coqui_tts(self, text, filepath, voice):
        """
        Use Coqui-TTS to generate speech and save it as a WAV file.
        """
        wav = self.synthesizer.tts(text)
        
        # Save the generated speech to a WAV file
        wav_output_path = filepath.replace(".mp3", ".wav")
        self.synthesizer.save_wav(wav, wav_output_path)

        # Optionally, you can convert the WAV to MP3 using a library or command (like ffmpeg)
        mp3_filepath = filepath.replace(".wav", ".mp3")
        self.convert_wav_to_mp3(wav_output_path, mp3_filepath)

    def convert_wav_to_mp3(self, wav_filepath, mp3_filepath):
        """
        Convert the WAV file to MP3 using a simple ffmpeg command.
        """
        ffmpeg_command = f'ffmpeg -i "{wav_filepath}" -codec:a libmp3lame -qscale:a 2 "{mp3_filepath}" -y'
        return_code = os.system(ffmpeg_command)

        if return_code != 0:
            print(f"Error: 'ffmpeg' command failed with return code {return_code}")
            return

        # Clean up the WAV file
        os.remove(wav_filepath)
