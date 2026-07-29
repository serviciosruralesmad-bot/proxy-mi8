import re
import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300  # Renueva cada 5 minutos

IFRAME_URL = "https://repro.arcast.cloud/canal8mdp/index.php"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://mi8.com.ar/"
}

def obtener_url_fresca():
    global cached_url, last_fetch_time
    ahora = time.time()
    
    if cached_url and (ahora - last_fetch_time < CACHE_DURATION):
        return cached_url

    try:
        print("Obteniendo señal desde el reproductor de Arcast...")
        res = requests.get(IFRAME_URL, headers=HEADERS, timeout=10)
        html = res.text
        print(f"Respuesta de Arcast: Status {res.status_code}")

        # 1. Buscar URL completa https://...m3u8
        match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if match:
            found_url = match.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
            print(f"¡URL encontrada con exito!: {found_url}")
            cached_url = found_url
            last_fetch_time = me_time = ahora
            return cached_url

        # 2. Buscar URL relativa //...m3u8 o rutas internas
        match_rel = re.search(r'//[^\s"\']+\.m3u8[^\s"\']*', html)
        if match_rel:
            found_url = "https:" + match_rel.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
            print(f"¡URL relativa encontrada!: {found_url}")
            cached_url = found_url
            last_fetch_time = me_time = ahora
            return cached_url

        # 3. Buscar cualquier coincidencia de archivo m3u8 o stream
        match_src = re.search(r'(source|file|src)\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if match_src:
            found_url = match_src.group(2).replace('\\/', '/')
            if not found_url.startswith('http'):
                found_url = 'https://repro.arcast.cloud/canal8mdp/' + found_url.lstrip('/')
            print(f"¡URL capturada de variable JS!: {found_url}")
            cached_url = found_url
            last_fetch_time = me_time = ahora
            return cached_url

        print("Contenido recibido de Arcast (primeros 300 caracteres):")
        print(html[:300])

    except Exception as e:
        print(f"Error en la peticion: {e}")

    return cached_url

@app.route('/')
def home():
    return "Proxy Mi8 activo"

@app.route('/mi8.m3u8')
def proxy_stream():
    url = obtener_url_fresca()
    if url:
        return redirect(url, code=302)
    return "Error al obtener la señal", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    return "Error al obtener la señal", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
