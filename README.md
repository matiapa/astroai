# 🔭 AstroGuide - Tu Guía Turístico del Cosmos

AstroGuide es un agente de IA que actúa como un astrónomo experto, brindando "información turística" fascinante sobre lo que estás viendo a través de tu telescopio.

## ✨ Características

- **Análisis de Imágenes**: Identifica automáticamente estrellas, nebulosas, galaxias y otros objetos celestes en tus fotos de telescopio
- **Narrativas Cautivadoras**: Transforma datos técnicos en historias fascinantes llenas de mitología, historia y curiosidades
- **Búsqueda Inteligente**: Complementa la información con búsquedas web para datos actualizados y curiosidades adicionales
- **Imágenes Anotadas**: Genera versiones anotadas de tus fotos con los objetos identificados y marcados

## 🚀 Instalación

### 1. Crear entorno virtual (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate  # En macOS/Linux
# o
.venv\Scripts\activate  # En Windows
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar API Keys

Crea un archivo `.env` en el directorio raíz con tus claves API:

```bash
echo 'GOOGLE_API_KEY="tu_clave_de_google"' > .env
echo 'ASTROMETRY_API_KEY="tu_clave_de_astrometry"' >> .env
```

**Obtener las claves:**
- **Google API Key** (para Gemini): https://aistudio.google.com/app/apikey
- **Astrometry.net API Key** (para plate solving): https://nova.astrometry.net/api_help

### Configuración opcional (variables de entorno)

```bash
# Timeout para plate solving en segundos (default: 120)
ASTROMETRY_TIMEOUT=180

# Usar cache de plate solving (default: true)
ASTROMETRY_USE_CACHE=true

# Directorio para cache (default: directorio temporal del sistema)
ASTROMETRY_CACHE_DIR=/path/to/cache
```

## 🎮 Uso

### Ejecutar con interfaz web (recomendado)

```bash
adk web --port 8000
```

Luego abre http://localhost:8000 en tu navegador, selecciona el agente `astro_guide` y empieza a chatear.

### Ejecutar desde línea de comandos

```bash
adk run astro_guide
```

## 💬 Cómo Usar

1. Toma una foto con tu telescopio o cámara astronómica
2. Pregúntale al agente: *"¿Qué estoy viendo?"* adjuntando tu imagen
3. El agente analizará la imagen, identificará los objetos y te contará su historia

### Ejemplo de conversación:

**Tú:** ¿Qué estoy viendo? [adjunta imagen]

**AstroGuide:** ¡Bienvenido a uno de los rincones más espectaculares del cielo invernal! 
Tu telescopio está apuntando hacia la constelación de Orión, específicamente a una región 
cercana al famoso Cinturón del Cazador...

*[El agente continúa con una narrativa fascinante sobre los objetos identificados]*

## 📁 Estructura del Proyecto

```
AstroIA/
├── astro_guide/           # Agente ADK
│   ├── agent.py           # Definición del agente y herramientas
│   └── __init__.py
├── annotator.py           # Módulo de análisis de imágenes
├── requirements.txt       # Dependencias
├── .env                   # Claves API (crear manualmente)
└── README.md
```

## 🛠️ Herramientas del Agente

### `analyze_telescope_image`
Analiza una imagen de telescopio usando plate-solving (Astrometry.net) y consulta catálogos astronómicos (SIMBAD, Hipparcos, NGC) para identificar todos los objetos visibles.

**Parámetros:**
- `image`: Imagen PIL del telescopio
- `search_radius`: Radio de búsqueda en grados (auto-calculado si no se especifica)
- `magnitude_limit`: Magnitud límite para objetos (default: 12.0)

**Retorna:**
- `success`: Si el análisis fue exitoso
- `annotated_image`: Imagen PIL anotada con los objetos marcados
- `plate_solving`: Coordenadas del centro (RA/DEC), campo de visión, escala de píxel
- `objects`: Lista de objetos con nombre, tipo, magnitud, tipo espectral, distancia

### `google_search`
Busca información adicional en internet sobre objetos celestes, constelaciones, mitología, y descubrimientos recientes.

## 📚 Uso del Módulo Annotator

El módulo `annotator.py` puede usarse de forma independiente:

```python
from annotator import analyze_image
from PIL import Image

# Cargar imagen
img = Image.open("telescope_capture.png")

# Analizar
result = analyze_image(img, radius=1.5, mag_limit=10.0)

if result["success"]:
    # Imagen anotada
    annotated = result["annotated_image"]
    annotated.save("annotated.png")
    
    # Información de objetos
    print(f"Centro: {result['plate_solving']['center']['ra_hms']}")
    print(f"Objetos: {result['objects']['count']}")
    
    for obj in result["objects"]["items"]:
        print(f"  - {obj['name']} ({obj['type']})")
```

## 🌟 Tips

- **Imágenes de buena calidad**: El plate-solving funciona mejor con imágenes nítidas que muestren suficientes estrellas
- **Tiempo de análisis**: La primera vez que analices una imagen puede tomar 1-2 minutos mientras Astrometry.net resuelve las coordenadas (luego se cachea)
- **Magnitud límite**: Ajusta `magnitude_limit` según necesites más objetos (valores altos) o solo los brillantes (valores bajos)

## 📝 Licencia

MIT

---

*"El universo no solo es más extraño de lo que suponemos, sino más extraño de lo que podemos suponer."* - J.B.S. Haldane

