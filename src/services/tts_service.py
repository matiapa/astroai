"""
TTS Service

Generates audio from text using the Gemini TTS API.
"""

import base64
import os
import wave
from typing import Optional, Tuple, Dict
import dotenv
from google import genai
from google.genai import types


def _save_wave_file(
    filename: str,
    pcm_data: bytes,
    channels: int = 1,
    rate: int = 24000,
    sample_width: int = 2
) -> None:
    """Save PCM audio data to a WAV file."""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm_data)


# Voice recommendations for common languages
LANGUAGE_VOICES: Dict[str, str] = {
    "es": "Aoede",   # Spanish - Female, warm
    "en": "Kore",    # English - Female, clear
    "fr": "Leda",    # French - Female, soft
    "de": "Puck",    # German - Male, friendly
    "it": "Aoede",   # Italian
    "pt": "Aoede",   # Portuguese
    "ja": "Kore",    # Japanese
    "ko": "Kore",    # Korean
    "zh": "Kore",    # Chinese
    "ru": "Charon",  # Russian - Male, deep
    "ar": "Charon",  # Arabic
    "hi": "Puck",    # Hindi
}

DEFAULT_VOICE = "Kore"


class TTSService:
    """Service for text-to-speech using Gemini TTS API."""
    
    VOICES = ["Aoede", "Puck", "Kore", "Charon", "Fenrir", "Leda"]
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        language: str = "es",
        voice: Optional[str] = None
    ):
        """
        Initialize the TTS service.
        
        Args:
            api_key: Google API key. If not provided, uses GOOGLE_API_KEY env var.
            language: ISO language code for voice selection and speech output.
            voice: Optional voice override.
        """
        dotenv.load_dotenv()
        
        if api_key is None:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash-preview-tts"
        self.language = language
        
        # Use provided voice or language default
        if voice and voice in self.VOICES:
            self.voice = voice
        else:
            self.voice = LANGUAGE_VOICES.get(language, DEFAULT_VOICE)
    
    def generate_audio(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> Tuple[bytes, Optional[str]]:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save the WAV file
        
        Returns:
            Tuple of (audio_bytes, saved_file_path)
        """
        # Prompt always in English, language specified for output
        content = f"""Speak in a warm, enthusiastic, and conversational tone. 
You are an expert astronomer sharing fascinating discoveries with wonder and awe.
Speak in {self.language} with natural pacing and emotional expression.

Text to speak:
{text}"""
        
        # Call Gemini TTS API
        response = self.client.models.generate_content(
            model=self.model,
            contents=content,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=self.voice,
                        )
                    ),
                ),
            )
        )
        
        # Extract audio data
        if (
            not response.candidates
            or not response.candidates[0].content
            or not response.candidates[0].content.parts
            or not response.candidates[0].content.parts[0].inline_data
            or not response.candidates[0].content.parts[0].inline_data.data
        ):
            raise ValueError("Failed to generate audio: empty response from TTS API")
        
        audio_data: bytes = response.candidates[0].content.parts[0].inline_data.data
        
        # Save to file if path provided
        saved_path: Optional[str] = None
        if output_path:
            _save_wave_file(output_path, audio_data)
            saved_path = output_path
        
        return audio_data, saved_path
    
    def generate_audio_base64(
        self,
        text: str,
        output_path: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Generate audio and return as base64 string.
        
        Args:
            text: Text to convert to speech
            output_path: Optional path to save the WAV file
        
        Returns:
            Tuple of (base64_encoded_audio, saved_file_path)
        """
        audio_bytes, saved_path = self.generate_audio(text, output_path)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return audio_base64, saved_path
