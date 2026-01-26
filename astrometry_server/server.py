from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Ruta donde se guardarán temporalmente los archivos
UPLOAD_FOLDER = '/tmp/astrometry'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/solve', methods=['POST'])
def solve():
    if 'image' not in request.files:
        return jsonify({"error": "No se subió ninguna imagen"}), 400
    
    img = request.files['image']
    base_name = "upload"
    img_path = os.path.join(UPLOAD_FOLDER, f"{base_name}.jpg")
    wcs_path = os.path.join(UPLOAD_FOLDER, f"{base_name}.wcs")
    
    # Limpiar archivos de ejecuciones anteriores
    for ext in ['.wcs', '.solved', '.axy', '.match', '.rdls']:
        if os.path.exists(os.path.join(UPLOAD_FOLDER, base_name + ext)):
            os.remove(os.path.join(UPLOAD_FOLDER, base_name + ext))

    img.save(img_path)
    
    # Comando optimizado para tu reflector 750/150 y oculares
    # Ajustamos el scale-low/high para cubrir de 12mm a 26mm
    cmd = [
        "solve-field", img_path,
        "--scale-units", "degwidth",
        "--scale-low", "0.5",
        "--scale-high", "3.0",
        "--downsample", "2",
        "--tweak-order", "3",
        "--no-plots",
        "--overwrite",
        "--resort",
        "--odds-to-solve", "1e9",
        "--dir", UPLOAD_FOLDER
    ]
    
    try:
        # Ejecutar el proceso
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Verificar si se generó el archivo .wcs
        if os.path.exists(wcs_path):
            with open(wcs_path, 'r') as f:
                wcs_content = f.read()
            return jsonify({
                "status": "success",
                "wcs": wcs_content
            })
        else:
            return jsonify({"status": "error", "message": "No se pudo resolver la imagen"}), 422
            
    except subprocess.CalledProcessError:
        return jsonify({"status": "error", "message": "Error ejecutando solve-field"}), 500

if __name__ == '__main__':
    # Usamos el puerto 8080 para evitar conflictos si el puerto 80 está ocupado
    app.run(host='0.0.0.0', port=80)