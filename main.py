import re
import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300  # Renueva el token cada 5 minutos

WEB_URL = "https://mi8.com.ar/en-vivo/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://mi8.com.ar/"
}

def obtener_url_fresca():
    global cached_url, last_fetch_time
    ahora = time.time()
    
    if cached_url and (ahora - last_fetch_time < CACHE_DURATION):
        return cached_url

    try:
        res = requests.get(WEB_URL, headers=HEADERS, timeout=8)
        match = re.search(r'https?://stream\.arcast\.ar/[^\s"\']+\.m3u8[^\s"\']*', res.text)
        if match:
            cached_url = match.group(0)
            last_fetch_time = ahora
            return cached_url
    except Exception as e:
        print(f"Error: {e}")

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
