import re
import time
import cloudscraper
from flask import Flask, redirect

app = Flask(__name__)

cached_url = None
last_fetch_time = 0
CACHE_DURATION = 300  # Guarda la URL por 5 minutos

# Scraper especial para evadir la pantalla de Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

TARGET_URL = "https://repro.arcast.cloud/canal8mdp/index.php"
WEB_URL = "https://mi8.com.ar/en-vivo/"

def obtener_url_fresca():
    global cached_url, last_fetch_time
    ahora = time.time()
    
    if cached_url and (ahora - last_fetch_time < CACHE_DURATION):
        return cached_url

    try:
        print("--- EVADIENDO CLOUDFLARE CON CLOUDSCRAPER ---")
        
        # 1. Probar en la pagina directa de Arcast
        res = scraper.get(TARGET_URL, timeout=12)
        print(f"Status Arcast con scraper: {res.status_code}")

        if res.status_code == 200:
            html = res.text
            match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if match:
                found_url = match.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
                print(f"¡URL encontrada con exito!: {found_url}")
                cached_url = found_url
                last_fetch_time = ahora
                return cached_url

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

        # 2. Respaldar buscando en la web principal de Mi8
        print("Buscando en mi8.com.ar con scraper...")
        res_mi8 = scraper.get(WEB_URL, timeout=12)
        if res_mi8.status_code == 200:
            match_mi8 = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', res_mi8.text)
            if match_mi8:
                found_url = match_mi8.group(0).replace('\\/', '/').split('"')[0].split("'")[0]
                print(f"¡URL encontrada en Mi8!: {found_url}")
                cached_url = found_url
                last_fetch_time = ahora
                return cached_url

    except Exception as e:
        print(f"Error en el scraping: {e}")

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
