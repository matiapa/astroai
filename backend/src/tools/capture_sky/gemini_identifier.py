"""
Gemini Structure Identifier

Uses Gemini Vision to identify the main astronomical structure in an image,
grounded by surrounding identified objects (stars).
"""

import os
import json
import base64
import dotenv
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from PIL import Image
import io

from src.config import AppConfig

IDENTIFICATION_PROMPT_TEMPLATE = """You are an expert astronomer. Your task is to identify the MAIN astronomical structure in this image.

## Context
I have already identified some stars/objects in this image to help you ground the location.
Here is the list of identified objects with their pixel coordinates (x,y) in the image:

{identified_objects_context}

## Image Data
Center Coordinates: RA {center_ra}, DEC {center_dec}
Pixel Scale: {pixel_scale} arcsec/pixel

## Instruction
Identify the single most prominent main structure in this image (e.g., a Nebula, Galaxy, Cluster, or a specific region of one).
The stars listed above should help you confirm the exact framing.
Do NOT output one of the stars in the grounding list as the main structure unless it is truly the striking feature (e.g. a bright planet).
Look for extended objects like Nebulas (e.g. Orion Nebula, Lagoon Nebula), Galaxies (e.g. Andromeda), or Star Clusters.

Return the result as a JSON object with the following fields:
- "name": The common name of the object (e.g., "M 42", "Orion Nebula", "Andromeda Galaxy"). This name will be used to query SIMBAD, so prefer catalog names like Messier (M) number or NGC number if available, or well-known common names.
- "pixel_coords": {{ "x": <approximate center x>, "y": <approximate center y>, "radius_pixels": <approximate radius> }} based on the image size.
- "confidence": A score from 0.0 to 1.0 indicating your confidence.
- "reasoning": A brief explanation of why you identified this object based on visual features and the grounded stars.

If you cannot identify any distinct main structure other than the stars provided, return null for the object data.

Output strictly valid JSON.
"""

class GeminiStructureIdentifier:
    def __init__(self, config: AppConfig):
        self.config = config
        self.api_key = config.gemini_api_key
        
        if not self.api_key:
             # Fallback to env var if not in config (though config usually loads it)
             self.api_key = os.environ.get("GOOGLE_API_KEY")

        if not self.api_key:
             print("Warning: No Gemini/Google API key found. GeminiStructureIdentifier will be disabled.")
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model = "gemini-2.0-flash" # Use a vision-capable model

    def identify_main_structure(
        self, 
        image: Image.Image,
        identified_objects: List[Dict[str, Any]],
        plate_solving: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Identify the main structure in the image.
        
        Args:
            image: PIL Image object
            identified_objects: List of currently identified objects (mostly stars)
            plate_solving: Plate solving info (ra, dec, scale)
            
        Returns:
            Dict with 'name', 'pixel_coords', etc., or None if failed/no key.
        """
        if not self.api_key:
            return None

        try:
            # 1. Format context
            context_str = self._format_objects_context(identified_objects)
            
            # 2. Build prompt
            prompt = IDENTIFICATION_PROMPT_TEMPLATE.format(
                identified_objects_context=context_str,
                center_ra=plate_solving.get("center_ra_deg"),
                center_dec=plate_solving.get("center_dec_deg"),
                pixel_scale=plate_solving.get("pixel_scale_arcsec")
            )

            # 3. Call Gemini
            # Resize image if too large to save bandwidth/tokens, though 2.0 Flash handles it well.
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
                ],
                config=types.GenerateContentConfig(
                    temperature=0.4, # Lower temperature for factual identification
                    response_mime_type="application/json",
                )
            )

            # 4. Parse result
            if not response.text:
                return None
            
            result = json.loads(response.text)
            
            # Validate essential fields
            if "name" in result and result.get("name"):
                 return result
            
            return None

        except Exception as e:
            print(f"Error in GeminiStructureIdentifier: {e}")
            return None

    def _format_objects_context(self, identified_objects: List[Dict[str, Any]]) -> str:
        lines = []
        for obj in identified_objects:
            name = obj.get("name", "Unknown")
            px = obj.get("pixel_coords", {}).get("x", "?")
            py = obj.get("pixel_coords", {}).get("y", "?")
            lines.append(f"- {name}: ({px}, {py})")
        
        if not lines:
            return "No objects identified yet."
        return "\n".join(lines[:20]) # Limit to top 20 to avoid clutter
