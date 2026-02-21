# Autor: Ing. Walter Rodríguez
# Fecha: 2026-02-20
# Descripción: Servidor Backend v3.0 con avatares GLB, voces neurales (edge-tts) y logs remotos.
# Cambio: Oculta la ventana de consola en Windows al iniciar.

import os
import sys
import ctypes

# ── Ocultar consola de Windows inmediatamente al arrancar ──────────────────────
# Esto funciona cuando se lanza con python.exe (no pythonw), evitando la ventana negra.
# Autor: Ing. Walter Rodríguez - 2026-02-20
if sys.platform == "win32":
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # SW_HIDE = 0
    except Exception:
        pass  # Si falla, ignora silenciosamente

import ssl
import requests as req_lib
from flask import Flask, render_template, request, jsonify, make_response, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import webview
import threading
import datetime
import asyncio
import edge_tts
import tempfile
import uuid
import socket
import json

# Archivo para persistir avatares personalizados
CUSTOM_AVATARS_FILE = 'custom_avatars.json'


# ======== Parche SSL Global ========
# Deshabilitar verificación SSL para redes con proxy/certificados auto-firmados.
# Afecta a aiohttp (usado por edge-tts) y a requests (descarga de avatares).
# Autor: Ing. Walter Rodríguez - 2026-02-18
_ssl_original_create_default_context = ssl.create_default_context
def _ssl_create_unverified_context(*args, **kwargs):
    ctx = _ssl_original_create_default_context(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
ssl.create_default_context = _ssl_create_unverified_context

# Cargar configuración
load_dotenv()

# Rutas base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'avatares')  # Cambiado a 'avatares' según solicitud
TTS_DIR = os.path.join(BASE_DIR, 'static', 'tts')

# Asegurar que las carpetas existan
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(TTS_DIR, exist_ok=True)

app = Flask(__name__, static_folder='static')
CORS(app)

# Servir archivos desde la carpeta 'avatares' fuera de static
from flask import send_from_directory
@app.route('/avatares/<path:filename>')
def serve_avatares(filename):
    return send_from_directory(MODELS_DIR, filename)

# Deshabilitar cache para que pywebview siempre sirva la versión más reciente
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/adaptar', methods=['POST'])
def adaptar_texto():
    """Usa Google Gemini para analizar el texto y agregar expresiones faciales automáticas.
    Autor: Ing. Walter Rodríguez - 2026-02-20
    Las expresiones se insertan como etiquetas: (feliz), (triste), (sorpresa), (enojo), (serio), (guiño)
    """
    data = request.get_json(silent=True) or {}
    texto = data.get('texto', '').strip()
    if not texto:
        return jsonify({"status": "error", "message": "No se proporcionó texto"}), 400

    google_api_key = os.getenv('Google-API-KEY', '').strip()
    if not google_api_key:
        return jsonify({"status": "error", "message": "Google-API-KEY no configurada en .env"}), 500

    # ── Expresiones faciales disponibles (ampliadas para mayor realismo) ──────
    # Autor: Ing. Walter Rodríguez - 2026-02-20
    prompt = f"""Eres un director de actuación para un avatar 3D hispanohablante.
Tu ÚNICA tarea es insertar etiquetas de expresión facial en el texto, \
para que el avatar se vea lo más natural y realista posible.

EXPRESIONES DISPONIBLES (úsalas EXACTAMENTE así, con paréntesis):
(feliz)   → alegría, entusiasmo, celebración
(triste)  → pena, nostalgia, dolor emocional
(enojo)   → molestia, frustración, indignación
(sorpresa)→ asombro, impacto, noticia inesperada
(guiño)   → complicidad, coqueteo, secreto
(serio)   → advertencia, énfasis, momento importante
(broma)   → humor, sarcasmo, tono juguetón
(llorar)  → llanto, emoción profunda, momento muy triste

REGLAS ESTRICTAS:
1. Inserta la etiqueta ANTES de la oración o frase que la necesita
2. Usa UNA etiqueta cada 2-3 oraciones como máximo (no abuses)
3. Si el texto es informativo/neutral, no pongas etiqueta
4. NO modifiques ninguna palabra del texto original
5. NO agregues explicaciones, introducciones ni comillas al responder
6. Responde ÚNICAMENTE el texto con las etiquetas insertadas

Texto a adaptar:
{texto}"""

    def _call_gemini(modelo, key, payload_data):
        """Llama a un modelo específico de Gemini. verify=False para proxy SSL."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={key}"
        return req_lib.post(url, json=payload_data, timeout=30, verify=False)

    def _get_available_models(key):
        """Obtiene la lista de modelos disponibles para esta API key."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        r = req_lib.get(url, timeout=15, verify=False)
        if r.status_code != 200:
            return []
        data = r.json()
        # Solo modelos que soporten generateContent y no sean de imagen/embedding
        excluir = ('image', 'embed', 'aqa', 'retrieval', 'robotics', 'computer-use', 'deep-research')
        modelos = []
        for m in data.get('models', []):
            nombre = m['name'].replace('models/', '')
            metodos = m.get('supportedGenerationMethods', [])
            if 'generateContent' in metodos and not any(x in nombre for x in excluir):
                modelos.append(nombre)
        # Ordenar: primero flash (más rápido), luego pro
        def orden(nombre):
            if 'flash' in nombre and 'lite' in nombre: return 0
            if 'flash' in nombre: return 1
            if 'pro' in nombre: return 2
            return 3
        modelos.sort(key=orden)
        return modelos

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048}
    }

    try:
        # ── Auto-descubrir modelos disponibles para esta API key ──────────────
        # Autor: Ing. Walter Rodríguez - 2026-02-20
        # Primero consultamos qué modelos tiene disponibles esta key específica
        modelos_disponibles = _get_available_models(google_api_key)
        print(f"[ADAPTAR] Modelos disponibles: {modelos_disponibles[:5]}...")

        if not modelos_disponibles:
            return jsonify({
                "status": "error",
                "message": (
                    "🔍 NO SE PUDIERON LISTAR LOS MODELOS\n\n"
                    "No se pudo conectar con Google para obtener los modelos disponibles.\n\n"
                    "Usa el botón '🔍 TEST API GEMINI' para diagnosticar.\n"
                    "Verifica tu conexión a internet."
                )
            }), 200

        resp = None
        modelo_usado = None

        for modelo in modelos_disponibles:
            r = _call_gemini(modelo, google_api_key, payload)
            if r.status_code == 200:
                resp = r
                modelo_usado = modelo
                print(f"[ADAPTAR] ✓ Usando: {modelo}")
                break
            elif r.status_code in (404, 400):
                print(f"[ADAPTAR] ✗ {modelo} → {r.status_code}")
                continue
            else:
                resp = r
                print(f"[ADAPTAR] Error {r.status_code} con {modelo}")
                break

        if resp is None:
            return jsonify({
                "status": "error",
                "message": (
                    "🔍 NINGÚN MODELO FUNCIONÓ\n\n"
                    f"Se probaron {len(modelos_disponibles)} modelos y ninguno respondió correctamente.\n\n"
                    "Usa el botón '🔍 TEST API GEMINI' para ver qué modelos tienes disponibles.\n"
                    "Puede ser un problema de cuota o permisos."
                )
            }), 200

        # ── Manejo descriptivo de errores por código HTTP ─────────────────────
        if resp.status_code != 200:
            try:
                err_body = resp.json()
                err_msg  = err_body.get('error', {}).get('message', resp.text[:300])
                err_code = err_body.get('error', {}).get('code', resp.status_code)
            except Exception:
                err_msg  = resp.text[:300]
                err_code = resp.status_code

            if resp.status_code == 429:
                msg = (
                    "⚠️ CUOTA DE GEMINI AGOTADA\n\n"
                    "Has superado el límite gratuito de la API de Google.\n\n"
                    "🔑 API Key: Google-API-KEY en tu archivo .env\n\n"
                    "Opciones:\n"
                    "• Espera unos minutos (cuota/minuto) o mañana (cuota/día)\n"
                    "• Nueva key gratuita en: aistudio.google.com\n"
                    "• Plan de pago en: console.cloud.google.com"
                )
            elif resp.status_code == 403:
                msg = (
                    "🚫 API KEY SIN PERMISOS\n\n"
                    "La Google-API-KEY en .env no tiene acceso a Gemini.\n\n"
                    "• Ve a aistudio.google.com → API Keys\n"
                    "• Genera una nueva key y actualiza el .env\n\n"
                    f"Detalle: {err_msg}"
                )
            elif resp.status_code == 400:
                msg = (
                    "📋 ERROR EN EL TEXTO\n\n"
                    "El texto es demasiado largo o tiene caracteres no permitidos.\n\n"
                    f"Detalle: {err_msg}"
                )
            else:
                msg = (
                    f"❌ ERROR GEMINI (HTTP {err_code})\n\n"
                    f"Revisa tu Google-API-KEY en el archivo .env\n\n"
                    f"Detalle: {err_msg}"
                )

            print(f"[ADAPTAR] Error HTTP {resp.status_code}: {err_msg}")
            return jsonify({"status": "error", "message": msg, "code": resp.status_code}), 200

        result = resp.json()
        texto_adaptado = result['candidates'][0]['content']['parts'][0]['text'].strip()
        print(f"[ADAPTAR] OK ({len(texto_adaptado)} chars) via {modelo_usado}")
        return jsonify({"status": "ok", "texto_adaptado": texto_adaptado, "modelo": modelo_usado})

    except req_lib.exceptions.Timeout:
        msg = "⏱️ TIEMPO DE ESPERA AGOTADO\n\nGemini no respondió en 30 segundos.\nVerifica tu conexión a internet."
        return jsonify({"status": "error", "message": msg}), 200

    except Exception as e:
        print(f"[ADAPTAR] Error inesperado: {e}")
        return jsonify({"status": "error", "message": f"❌ Error inesperado: {str(e)}"}), 500


@app.route('/test-api', methods=['GET'])
def test_api():
    """Endpoint para verificar si la Google-API-KEY funciona y qué modelos tiene disponibles.
    Autor: Ing. Walter Rodríguez - 2026-02-20
    """
    google_api_key = os.getenv('Google-API-KEY', '').strip()
    if not google_api_key:
        return jsonify({
            "status": "error",
            "message": "Google-API-KEY no está configurada en el archivo .env"
        })

    try:
        # Listar modelos disponibles para esta API key
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={google_api_key}"
        resp = req_lib.get(url, timeout=15, verify=False)

        if resp.status_code == 200:
            data = resp.json()
            modelos = [m['name'].replace('models/', '') for m in data.get('models', [])
                       if 'generateContent' in m.get('supportedGenerationMethods', [])]
            return jsonify({
                "status": "ok",
                "key_preview": f"{google_api_key[:8]}...{google_api_key[-4:]}",
                "modelos_disponibles": modelos,
                "total": len(modelos)
            })
        elif resp.status_code == 400:
            return jsonify({"status": "error", "message": "API Key inválida o mal formada", "http": 400})
        elif resp.status_code == 403:
            return jsonify({"status": "error", "message": "API Key sin permisos para Gemini API", "http": 403})
        else:
            return jsonify({"status": "error", "message": f"Error HTTP {resp.status_code}", "detalle": resp.text[:200]})

    except req_lib.exceptions.Timeout:
        return jsonify({"status": "error", "message": "Timeout: no se pudo conectar con Google en 15 segundos"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})




@app.route('/log', methods=['POST'])
def log_from_client():
    """Recibe logs del frontend y los imprime en la terminal."""
    data = request.json
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    level = data.get('level', 'INFO').upper()
    message = data.get('message', '')
    print(f"[{timestamp}] [CLIENT-{level}] {message}")
    return jsonify({"status": "ok"})

@app.route('/check-models')
def check_models():
    """Verifica qué modelos GLB existen localmente."""
    os.makedirs(MODELS_DIR, exist_ok=True)
    models = [f for f in os.listdir(MODELS_DIR) if f.endswith('.glb')]
    return jsonify({"models": models, "path": "/static/models/"})

@app.route('/download-sample-avatar', methods=['POST'])
def download_sample_avatar():
    """Descarga modelos GLB compatibles con TalkingHead.
    Autor: Ing. Walter Rodríguez - 2026-02-20
    Acepta un avatar_id del catálogo O una custom_url directa."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Parámetros de calidad ARKit+Oculus para ReadyPlayerMe
    morph_params = "?morphTargets=ARKit,Oculus+Visemes,mouthOpen,mouthSmile,eyesClosed,eyesLookUp,eyesLookDown&textureSizeLimit=1024&textureFormat=png&pose=T"

    # Catálogo base (IDs verificados con gender)
    # Nota: Los IDs de RPM pueden variar. Si un avatar da 404, usar URL personalizada.
    catalog = {
        'avatar_default': {
            'name': 'Femenino Realista',
            'gender': 'F',
            'url': f"https://models.readyplayer.me/64bfa15f0e72c63d7c3934a6.glb{morph_params}"
        },
        'avatar_f2': {
            'name': 'Mara Femenina',
            'gender': 'F',
            'url': f"https://models.readyplayer.me/63bc9cb9c0c20de6c48cd8f8.glb{morph_params}"
        },
        'avatar_male': {
            'name': 'Masculino Realista',
            'gender': 'M',
            'url': f"https://models.readyplayer.me/64bfa4a6ce0a8563cd28148e.glb{morph_params}"
        }
    }

    # Agregar avatares personalizados guardados
    if os.path.exists(CUSTOM_AVATARS_FILE):
        try:
            with open(CUSTOM_AVATARS_FILE, 'r') as f:
                catalog.update(json.load(f))
        except:
            pass

    # Leer parámetros de la solicitud
    data = request.get_json(silent=True) or {}
    avatar_id   = data.get('avatar_id', '').strip()
    custom_url  = data.get('custom_url', '').strip()

    # --- Caso A: URL personalizada enviada directamente ---
    if custom_url:
        # Agregar morphTargets si es RPM sin parámetros
        if 'readyplayer.me' in custom_url and '?' not in custom_url:
            custom_url += morph_params
        uid = uuid.uuid4().hex[:6]
        avatar_id = f'custom_{uid}'
        # Persistir para la galería
        custom_entry = {avatar_id: {'name': f'Personalizado {uid}', 'gender': 'F', 'url': custom_url}}
        existing = {}
        if os.path.exists(CUSTOM_AVATARS_FILE):
            try:
                with open(CUSTOM_AVATARS_FILE, 'r') as fp:
                    existing = json.load(fp)
            except:
                pass
        existing.update(custom_entry)
        with open(CUSTOM_AVATARS_FILE, 'w') as fp:
            json.dump(existing, fp, indent=2)
        download_url = custom_url
        avatar_name = f'Personalizado {uid}'

    # --- Caso B: ID del catálogo ---
    elif avatar_id and avatar_id in catalog:
        download_url = catalog[avatar_id]['url']
        avatar_name  = catalog[avatar_id]['name']

    else:
        return jsonify({"status": "error", "message": "Debes enviar custom_url o un avatar_id válido."}), 400

    # Ruta destino
    target_file = os.path.join(MODELS_DIR, f'{avatar_id}.glb')

    # No re-descargar si ya existe y es válido
    if os.path.exists(target_file) and os.path.getsize(target_file) > 100_000:
        size_mb = os.path.getsize(target_file) / (1024 * 1024)
        print(f"[DOWNLOAD] {avatar_name} ya existe ({size_mb:.1f} MB), omitiendo.")
        return jsonify({"status": "ok", "message": f"Ya descargado ({size_mb:.1f} MB)", "path": f"/avatares/{avatar_id}.glb", "avatar_id": avatar_id})

    # Descargar
    try:
        print(f"[DOWNLOAD] Descargando '{avatar_name}' desde: {download_url[:70]}...")
        resp = req_lib.get(download_url, timeout=90, stream=True, verify=False)
        if resp.status_code == 200:
            with open(target_file, 'wb') as fp:
                for chunk in resp.iter_content(chunk_size=8192):
                    fp.write(chunk)
            size_mb = os.path.getsize(target_file) / (1024 * 1024)
            print(f"[DOWNLOAD] Completado: {avatar_name} ({size_mb:.1f} MB)")
            return jsonify({"status": "ok", "message": f"Descargado ({size_mb:.1f} MB)", "path": f"/avatares/{avatar_id}.glb", "avatar_id": avatar_id})
        else:
            return jsonify({"status": "error", "message": f"Error HTTP {resp.status_code} - Avatar no disponible en la nube. Usa el creador de avatares en https://readyplayer.me para obtener tu propio enlace .glb"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/avatars')
def list_avatars():
    """Lista SOLO los avatares descargados en la carpeta local 'avatares/'.
    Autor: Ing. Walter Rodríguez - 2026-02-20
    Cambio: eliminado catálogo nube. Solo muestra lo que hay en disco."""

    # Cargar metadatos de avatares personalizados (nombre, género guardados al descargar)
    metadata = {}
    if os.path.exists(CUSTOM_AVATARS_FILE):
        try:
            with open(CUSTOM_AVATARS_FILE, 'r') as f:
                metadata = json.load(f)
        except:
            pass

    # Nombres amigables para avatares del catálogo base
    base_names = {
        'avatar_default': {'name': 'Femenino Realista', 'gender': 'F'},
    }

    # Escanear SOLO la carpeta avatares/ en disco
    res_list = []
    if os.path.exists(MODELS_DIR):
        for filename in sorted(os.listdir(MODELS_DIR)):
            if not filename.endswith('.glb'):
                continue
            aid = filename.replace('.glb', '')
            # Prioridad: base_names > custom_avatars.json > nombre derivado del filename
            info = base_names.get(aid) or metadata.get(aid) or {}
            res_list.append({
                'id': aid,
                'name': info.get('name', aid.replace('_', ' ').title()),
                'gender': info.get('gender', 'F'),
                'path': f'/avatares/{filename}',
                'is_local': True
            })

    return jsonify({"status": "ok", "avatars": res_list})


# ======== Voces Neurales con Edge-TTS ========
@app.route('/tts-voices')
def tts_voices():
    """Lista las voces neurales disponibles (Microsoft Edge).
    Autor: Ing. Walter Rodríguez - 2026-02-18"""
    try:
        loop = asyncio.new_event_loop()
        voices = loop.run_until_complete(edge_tts.list_voices())
        loop.close()
        
        # Filtrar voces Priorizando 'Neural' y español/inglés
        filtered_voices = [v for v in voices if "Neural" in v['ShortName'] and (v['Locale'].startswith('es-') or v['Locale'] == 'en-US')]
        
        result = []
        for v in filtered_voices:
            friendly = f"{v['FriendlyName']} ({v['Locale']})"
            result.append({
                'name': v['ShortName'],
                'friendlyName': friendly,
                'locale': v['Locale'],
                'gender': v['Gender']
            })
            
        # Ordenar: primero español
        result.sort(key=lambda x: (not x['locale'].startswith('es'), x['locale']))
        
        return jsonify({"status": "ok", "voices": result})
    except Exception as e:
        print(f"[TTS-VOICES] Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Genera audio con Microsoft Edge-TTS (Gratis y Neural).
    Autor: Ing. Walter Rodríguez - 2026-02-18"""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '').strip()
    # Voz por defecto: Ramona (Republica Dominicana)
    voice = data.get('voice', 'es-DO-RamonaNeural')
    rate = data.get('rate', '+0%')
    
    if not text:
        return jsonify({"status": "error", "message": "No se proporcionó texto"}), 400
    
    os.makedirs(TTS_DIR, exist_ok=True)
    audio_filename = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    audio_path = os.path.join(TTS_DIR, audio_filename)
    
    try:
        async def generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(audio_path)
            
        loop = asyncio.new_event_loop()
        loop.run_until_complete(generate())
        loop.close()
        
        print(f"[TTS] Audio generado: {audio_filename} ({voice})")
        
        # Limpieza automática
        try:
            tts_files = sorted(
                [f for f in os.listdir(TTS_DIR) if f.startswith('tts_')],
                key=lambda f: os.path.getmtime(os.path.join(TTS_DIR, f))
            )
            while len(tts_files) > 10:
                os.remove(os.path.join(TTS_DIR, tts_files.pop(0)))
        except:
            pass
            
        return jsonify({
            "status": "ok",
            "audio_url": f"/static/tts/{audio_filename}"
        })
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def run_flask():
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. Verificar si ya se está ejecutando (Single Instance Check)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Intentar enlazar al puerto Flask (5000) de forma temporal para ver si está libre.
        # Nota: Flask usa el puerto, así que si bind falla, Flask ya está corriendo.
        # Pero Flask tarda en iniciar. Mejor: intentar CONECTAR. Si conecta, ya existe.
        sock.connect(('127.0.0.1', 5000))
        print("¡La aplicación ya está en ejecución! (Puerto 5000 ocupado)")
        sock.close()
        sys.exit()
    except ConnectionRefusedError:
        # Nadie escucha en el puerto, estamos libres para iniciar.
        pass
    finally:
        sock.close()

    # Crear carpeta de modelos si no existe
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Calcular posición centrada usando ctypes (Windows API)
    # IMPORTANTE: NO llamar SetProcessDPIAware() aquí para mantener píxeles lógicos
    # que es el sistema de coordenadas que espera pywebview en Windows.
    # Autor: Ing. Walter Rodríguez - 2026-02-20
    import ctypes, time
    user32 = ctypes.windll.user32
    screen_w = user32.GetSystemMetrics(0)  # píxeles LÓGICOS (sin DPI override)
    screen_h = user32.GetSystemMetrics(1)
    win_w, win_h = 1000, 850
    pos_x = (screen_w - win_w) // 2
    pos_y = (screen_h - win_h) // 2
    print(f"[APP] Pantalla: {screen_w}x{screen_h} → Ventana centrada en ({pos_x},{pos_y})")

    # Iniciar Flask en un hilo separado
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Esperar que Flask esté listo antes de abrir la ventana (evita ventana en blanco)
    print("[APP] Esperando que Flask esté listo...")
    for _ in range(40):  # máx 4 segundos
        try:
            test = socket.create_connection(("127.0.0.1", 5000), timeout=0.1)
            test.close()
            print("[APP] Flask listo ✓")
            break
        except OSError:
            time.sleep(0.1)

    # Crear la ventana sin x/y - se centrara en el evento shown
    print("Iniciando aplicación Avatar 3D...")
    window = webview.create_window(
        'Avatar IA - Ing. Walter Rodriguez',
        'http://127.0.0.1:5000',
        width=win_w,
        height=win_h,
        min_size=(800, 600)
    )

    # Centrar via evento shown: se dispara cuando la ventana ya es visible
    # Esto es más confiable que pasar x/y al constructor (evita bugs de DPI)
    def mover_al_centro():
        try:
            window.move(pos_x, pos_y)
            print(f"[APP] Ventana movida a ({pos_x}, {pos_y}) ✓")
        except Exception as e:
            print(f"[APP] No se pudo centrar: {e}")

    # Al cerrar la ventana del avatar, terminar TODO el proceso (Flask + hilo)
    # Esto libera el puerto 5000 y permite reabrir la app sin problemas
    # Autor: Ing. Walter Rodríguez - 2026-02-20
    def al_cerrar():
        print("[APP] Ventana cerrada → terminando proceso completo...")
        os._exit(0)  # Termina proceso completo incluyendo hilo Flask

    window.events.shown  += mover_al_centro
    window.events.closed += al_cerrar

    webview.start(debug=False)

    # Fallback si webview.start() retorna sin disparar closed
    sys.exit(0)

