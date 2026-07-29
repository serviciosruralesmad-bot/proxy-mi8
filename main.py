import re
import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300  # Guarda la URL por 5 minutos

TARGET_URL = "https://repro.arcast.cloud/canal8mdp/index.php"
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
        print("--- BUSCANDO SEÑAL EN ARCAST ---")
        res = requests.get(TARGET_URL, headers=HEADERS, timeout=10)
        html = res.text
        print(f"Status Arcast: {res.status_code}")

        # 1. Buscar URL completa de m3u8
        match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if match:
            found_url = match.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
            print(f"¡URL encontrada!: {found_url}")
            cached_url = found_url
            last_fetch_time = ahora
            return cached_url

        # 2. Buscar URLs sin protocolo o dentro de comillas
        match_rel = re.search(r'["\']([^"\']+\.m3u8[^"\']*)["\']', html)
        if match_rel:
            found_url = match_rel.group(1).replace('\\/', '/')
            if found_url.startswith('//'):
                found_url = "https:" + found_url
            elif not found_url.startswith('http'):
                found_url = "https://repro.arcast.cloud/canal8mdp/" + found_url.lstrip('/')
            print(f"¡URL encontrada (relativa)!: {found_url}")
            cached_url = found_url
            last_fetch_time = ahora
            return cached_url

        print("HTML recibido de Arcast (primeros 500 caracteres):")
        print(html[:500])

    except Exception as e:
        print(f"Error en peticion: {e}")

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
