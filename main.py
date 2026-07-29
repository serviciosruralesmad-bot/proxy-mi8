import re
import time
import requests
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300  # Renueva cada 5 minutos

WEB_URL = "https://mi8.com.ar/en-vivo/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://mi8.com.ar/",
    "Accept-Language": "es-ES,es;q=0.9"
}

def obtener_url_fresca():
    global cached_url, last_fetch_time
    ahora = time.time()
    
    if cached_url and (ahora - last_fetch_time < CACHE_DURATION):
        return cached_url

    try:
        print("Iniciando busqueda de señal...")
        session = requests.Session()
        res = session.get(WEB_URL, headers=HEADERS, timeout=10)
        print(f"Respuesta de mi8.com.ar: Status {res.status_code}")

        html_acumulado = res.text

        # Buscar reproductor metido dentro de un iframe
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', res.text, re.IGNORECASE)
        print(f"Iframes detectados: {iframes}")

        for iframe_url in iframes:
            if any(k in iframe_url for k in ['stream', 'player', 'arcast', 'live', 'embed', 'vivo']):
                try:
                    if iframe_url.startswith('//'):
                        iframe_url = 'https:' + iframe_url
                    elif iframe_url.startswith('/'):
                        iframe_url = 'https://mi8.com.ar' + iframe_url

                    print(f"Analizando iframe: {iframe_url}")
                    iframe_res = session.get(iframe_url, headers=HEADERS, timeout=8)
                    html_acumulado += "\n" + iframe_res.text
                except Exception as ie:
                    print(f"Error en iframe {iframe_url}: {ie}")

        # Buscar cualquier archivo .m3u8 en todo el HTML
        match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html_acumulado)
        if match:
            found_url = match.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
            print(f"¡URL encontrada con exito!: {found_url}")
            cached_url = found_url
            last_fetch_time = ahora
            return cached_url

        print("No se encontro enlace .m3u8 en el sitio.")

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
