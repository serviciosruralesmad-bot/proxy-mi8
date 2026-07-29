import re
import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300

WEB_URL = "https://mi8.com.ar/en-vivo/"
IFRAME_URL = "https://repro.arcast.cloud/canal8mdp/index.php"

# Encabezados de navegador completo para superar Cloudflare
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://mi8.com.ar/",
    "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

# URLs directas conocidas de emisión de Arcast por si falla el scraping
FALLBACK_URLS = [
    "https://stream.arcast.cloud/canal8mdp/live/playlist.m3u8",
    "https://repro.arcast.cloud/canal8mdp/live.m3u8",
    "https://stream.arcast.cloud/canal8mdp/playlist.m3u8",
    "https://live.arcast.cloud/canal8mdp/index.m3u8"
]

def obtener_url_fresca():
    global cached_url, last_fetch_time
    ahora = time.time()
    
    if cached_url and (ahora - last_fetch_time < CACHE_DURATION):
        return cached_url

    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. Intentar navegación con sesión completa (Mi8 -> Arcast)
    try:
        print("Paso 1: Estableciendo sesion en Mi8...")
        session.get(WEB_URL, timeout=8)
        
        print("Paso 2: Obteniendo iframe de Arcast...")
        res = session.get(IFRAME_URL, timeout=8)
        print(f"Status Arcast: {res.status_code}")

        if res.status_code == 200:
            match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', res.text)
            if match:
                found_url = match.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
                print(f"¡URL encontrada via scraping!: {found_url}")
                cached_url = found_url
                last_fetch_time = ahora
                return cached_url
    except Exception as e:
        print(f"Error en scraping: {e}")

    # 2. Si Cloudflare da 403, probar transmisiones directas de Arcast
    print("Paso 3: Probando servidores de emision directa...")
    for candidate_url in FALLBACK_URLS:
        try:
            check = session.head(candidate_url, timeout=5, allow_redirects=True)
            if check.status_code in [200, 302]:
                print(f"¡Servidor directo activo encontrado!: {candidate_url}")
                cached_url = candidate_url
                last_fetch_time = ahora
                return cached_url
        except Exception:
            continue

    # Si todo falla pero teníamos una URL anterior, la devolvemos
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
