"""
Narration Generator Service

Generates narration text, title, and object legends using the Gemini API
for astronomical sky analysis results.
"""

from typing import List, Dict, Any, Optional
import os
import json
import dotenv
from google import genai
from google.genai import types


# Prompt template - always in English, with language code placeholder
NARRATION_PROMPT_TEMPLATE = """You are an expert astronomer and night sky tour guide. Your task is to generate a captivating narration about what is observed in a sky image.

## Image Data

**Central coordinates:** RA {center_ra}°, DEC {center_dec}°
**Pixel scale:** {pixel_scale} arcsec/pixel

**Identified objects:**
{objects_description}

## Your Task

Generate a JSON with the following exact format:

```json
{{
    "title": "A short, evocative title for the sky region (maximum 10 words)",
    "text": "A narration of 2-3 paragraphs in conversational prose, without lists or markdown formatting. Describe the most interesting objects, their cosmic context, and fascinating facts. Write as if you are guiding someone looking through a telescope.",
    "object_legends": {{
        "object_name_1": "A legend of 1-2 sentences describing unique characteristics of the object",
        "object_name_2": "Another legend..."
    }}
}}
```

## Important Rules

1. **Language**: Respond in {language_code}
2. **No lists**: The narration must be fluid prose, optimized to be read aloud (TTS)
3. **Fascinating data**: Include distances, ages, comparative sizes
4. **Context**: Mention constellations, mythology, or history when relevant
5. **Legends**: Generate a legend for EACH identified object
6. **JSON only**: Your response must be only valid JSON, no additional text"""


def _format_objects_for_prompt(identified_objects: List[Dict[str, Any]]) -> str:
    """Format identified objects for the prompt."""
    if not identified_objects:
        return "No specific objects were identified in this image."
    
    lines = []
    for obj in identified_objects:
        name = obj.get("name", "Unknown")
        obj_type = obj.get("type", "")
        subtype = obj.get("subtype", "")
        magnitude = obj.get("magnitude_visual")
        distance = obj.get("distance_lightyears")
        spectral = obj.get("spectral_type", "")
        
        parts = [f"- **{name}**"]
        if obj_type:
            parts.append(f"Type: {obj_type}")
        if subtype:
            parts.append(f"Subtype: {subtype}")
        if magnitude is not None:
            parts.append(f"Magnitude: {magnitude}")
        if distance is not None:
            parts.append(f"Distance: {distance} light-years")
        if spectral:
            parts.append(f"Spectral type: {spectral}")
        
        lines.append(", ".join(parts))
    
    return "\n".join(lines)


class NarrationGenerator:
    """Service for generating narration using Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the narration generator.
        
        Args:
            api_key: Google API key. If not provided, uses GOOGLE_API_KEY env var.
        """
        dotenv.load_dotenv()
        
        if api_key is None:
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3-flash-preview"
    
    def generate(
        self,
        plate_solving: Dict[str, Any],
        identified_objects: List[Dict[str, Any]],
        language: str = "es"
    ) -> Dict[str, Any]:
        """
        Generate narration for the sky analysis.
        
        Args:
            plate_solving: Dict with center_ra_deg, center_dec_deg, pixel_scale_arcsec
            identified_objects: List of identified celestial objects
            language: ISO language code (default: "es")
        
        Returns:
            Dict with title, text, and object_legends
        """
        # Build the prompt
        objects_description = _format_objects_for_prompt(identified_objects)
        
        prompt = NARRATION_PROMPT_TEMPLATE.format(
            center_ra=plate_solving.get("center_ra_deg", "N/A"),
            center_dec=plate_solving.get("center_dec_deg", "N/A"),
            pixel_scale=plate_solving.get("pixel_scale_arcsec", "N/A"),
            objects_description=objects_description,
            language_code=language
        )
        
        # Call Gemini API
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )
        
        # Parse response
        try:
            response_text = response.text
            if not response_text:
                raise ValueError("Empty response from Gemini API")
            
            result = json.loads(response_text)
            
            # Validate required fields
            if "title" not in result:
                result["title"] = "The Night Sky"
            if "text" not in result:
                result["text"] = "Could not generate a narration."
            if "object_legends" not in result:
                result["object_legends"] = {}
            
            return result
            
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a default response
            return {
                "title": "The Night Sky",
                "text": response.text if response.text else "Could not generate a narration.",
                "object_legends": {}
            }
