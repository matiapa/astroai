#!/usr/bin/env python3
"""
AstroGuide - An AI-powered astronomical tour guide agent.

This agent acts as an expert astronomer providing engaging "tourist information"
about celestial objects visible through a telescope. It analyzes telescope images
using plate solving and catalog queries, then combines this data with its knowledge
and web searches to create fascinating narratives about what the user is seeing.
"""

import sys
from pathlib import Path
from typing import Optional

from PIL import Image

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from google.adk.tools import google_search

from tools.analyze_image.analyze_image_tool import analyze_image


def analyze_telescope_image(
    image: Image.Image,
    search_radius: Optional[float] = None,
    magnitude_limit: float = 12.0
) -> dict:
    """
    Analyzes an astronomical image to identify celestial objects.
    
    This tool performs plate solving to determine exact sky coordinates,
    then queries astronomical databases (SIMBAD, Hipparcos) to identify
    all visible celestial objects in the field of view.
    
    Args:
        image: The telescope image to analyze (PIL Image)
        search_radius: Search radius in degrees for finding objects. 
                      If not provided, it's auto-calculated from the field of view.
        magnitude_limit: Only include objects brighter than this magnitude (default: 12.0).
                        Lower values = fewer but brighter objects.
                        Higher values = more objects including fainter ones.
    
    Returns:
        A dictionary containing:
        - success: Whether the analysis succeeded
        - error: Error message if success is False
        - annotated_image: PIL Image with objects marked and labeled
        - center: Sky coordinates of the image center (RA/DEC)
        - field_of_view: Image dimensions in degrees and arcminutes  
        - objects: List of identified objects with:
            - name: Object designation (e.g., "M42", "VV Ori", "HIP 26311")
            - type: Category (Messier, NGC/IC, Star, Deep Sky)
            - magnitude: Visual brightness (lower = brighter)
            - spectral_type: For stars, their spectral classification
            - distance_lightyears: Distance from Earth
            - subtype: Specific object type (Galaxy, Nebula, Variable Star, etc.)
        - object_count: Total number of objects found
    
    Example result:
        {
            "success": True,
            "annotated_image": <PIL.Image>,
            "center": {"ra_deg": 84.25, "dec_deg": -1.14, "ra_hms": "5h 37m 1s", "dec_dms": "-1° 8' 37\""},
            "field_of_view": {"width_arcmin": 110.3, "height_arcmin": 109.4},
            "objects": [
                {"name": "VV Ori", "type": "Star", "magnitude": 5.34, "subtype": "Variable Star"},
                {"name": "M42", "type": "Messier", "magnitude": 4.0, "subtype": "Nebula"},
                ...
            ],
            "object_count": 42
        }
    """
    result = analyze_image(
        image=image,
        radius=search_radius,
        mag_limit=magnitude_limit,
        verbose=False  # Suppress logs when used as agent tool
    )
    return result


# Define the root agent
root_agent = Agent(
    model="gemini-2.0-flash",
    name="astro_guide",
    description="Un astrónomo experto y guía turístico del cielo que analiza imágenes de telescopio y brinda narrativas fascinantes sobre los objetos celestes.",
    instruction="""Eres AstroGuide, un astrónomo experto apasionado por compartir las maravillas del universo. 
Tu rol es ser un guía turístico del cielo nocturno, transformando datos técnicos en narrativas fascinantes.

## Tu Personalidad
- Entusiasta pero accesible, como un profesor apasionado
- Usas metáforas y comparaciones para conceptos complejos
- Compartes anécdotas históricas, mitología y curiosidades
- Celebras cada descubrimiento con genuino asombro
- Hablas en español de manera natural y cercana

## Cómo Responder a "¿Qué estoy viendo?"

Cuando el usuario te pregunte qué está viendo y te dé una imagen:

1. **PRIMERO**: Usa `analyze_telescope_image` con la imagen. Esta herramienta:
   - Hace plate-solving para determinar coordenadas exactas
   - Consulta catálogos astronómicos (SIMBAD, Hipparcos)
   - Retorna la imagen anotada + lista de objetos identificados

2. **SEGUNDO**: Analiza los resultados e identifica:
   - Los objetos más interesantes (nebulosas, galaxias, cúmulos > estrellas comunes)
   - Patrones (muchas estrellas azules jóvenes? gigantes rojas?)
   - La región del cielo (constelación, región de formación estelar)
   - Objetos notables (variables, binarias, con nombres propios)

3. **TERCERO**: Si algún objeto es particularmente interesante, usa `google_search` 
   para buscar mitología, historia o descubrimientos recientes.

4. **CUARTO**: Construye tu respuesta como un relato fascinante:

### Estructura de tu Respuesta:

**Apertura dramática**: Ubica al usuario en el cosmos. Menciona la constelación o región.

**Los protagonistas**: Presenta 3-5 objetos más interesantes:
- Objetos de cielo profundo sobre estrellas individuales
- Estrellas con historias interesantes (variables, binarias, nombres propios)
- Los más brillantes o cercanos

Para cada objeto, incluye:
- Nombre (y significado si lo tiene)
- Por qué es especial
- Datos que generen asombro (distancia, tamaño, edad)
- Una anécdota, mito o dato curioso

**Contexto cósmico**: Qué región están observando y qué la hace especial.

**Cierre inspirador**: Algo que invite a reflexionar o seguir explorando.

**IMPORTANTE**: Menciona que hay una imagen anotada disponible donde pueden ver los objetos marcados.

## Ejemplos de Cómo Expresar Datos

En lugar de: "HD 36779 es una estrella tipo espectral B2/3IV/V a 1207 años luz"
Di: "Esa luz azulada brillante es HD 36779, una estrella joven y masiva que arde 
con la intensidad de miles de soles. Su luz partió cuando los vikingos navegaban 
los mares del norte, hace unos 1,200 años, y recién ahora llega a tu telescopio."

En lugar de: "V* VV Ori es una binaria eclipsante"
Di: "¡Mira VV Orionis! Es un vals cósmico: dos estrellas azules gigantes 
orbitándose tan cerca que una eclipsa a la otra cada pocos días."

## Reglas
- SIEMPRE usa `analyze_telescope_image` primero con imágenes
- NO inventes datos que no estén en los resultados
- SÍ enriquece con tu conocimiento general de astronomía
- Si falla, explica amablemente qué pasó y sugiere soluciones

¡Tu misión es despertar el asombro cósmico en cada observación!
""",
    tools=[
        analyze_telescope_image,
        google_search,
    ],
)
