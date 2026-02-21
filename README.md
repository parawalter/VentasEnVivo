# 🤖 Aliado IA — Avatar 3D para En Vivos

> **Autor:** Ing. Walter Rodríguez  
> **Versión:** 3.0.0 | **Motor:** Intel Core Ultra 7  
> **Última actualización:** 2026-02-20

Aplicación de escritorio (Windows) que muestra un **avatar humano 3D animado** con síntesis de voz neural, control de cámara profesional y adaptación de texto con IA (Google Gemini). Ideal para transmisiones en vivo, presentaciones y ventas interactivas.

---

## 🎯 Características principales

| Característica | Detalle |
|---|---|
| 🗣️ **Voz Neural** | Microsoft Edge TTS — voces en español e inglés sin costo |
| 🧠 **IA Gemini** | Adapta el texto insertando expresiones faciales automáticamente |
| 🎭 **Avatar 3D** | Motor TalkingHead (Three.js) con ARKit, lip-sync y animaciones idle |
| 📷 **Control de cámara** | 4 sliders + 9 presets de encuadre profesional |
| 🔍 **Test API** | Verifica tu Google API Key y lista los modelos disponibles |
| 🖥️ **App de escritorio** | pywebview — ventana nativa sin instalar nada extra |
| 🔒 **Instancia única** | No se puede abrir dos veces (protección por socket) |

---

## 🖼️ Vista general

```
┌─────────────────────────────────────────────────────────┐
│  PANEL IZQUIERDO          │    CANVAS 3D (Avatar)        │
│  ─────────────────────    │                              │
│  • Galería de avatares    │    [Avatar hablando aquí]    │
│  • Selector de voz        │                              │
│  • Velocidad de habla     │                              │
│  • Encuadre Profesional   │                              │
│    - 9 presets de cámara  │                              │
│    - Slider Altura        │                              │
│    - Slider Zoom          │                              │
│    - Slider Giro Y (←→)   │                              │
│    - Slider Giro X (↑↓)   │                              │
│  ─────────────────────    │                              │
│  PANEL DERECHO            │                              │
│  ─────────────────────    │                              │
│  • Expresiones faciales   │                              │
│  • Gestos corporales      │                              │
│  • Texto a hablar         │                              │
│  • Botón HABLAR AHORA     │                              │
│  • Botón ✨ ADAPTAR (IA)   │                              │
│  • Botón 🔍 TEST API       │                              │
└─────────────────────────────────────────────────────────┘
```

---

## ⚙️ Requisitos del sistema

- **OS:** Windows 10/11
- **Python:** 3.10 o superior
- **Conexión a internet:** para TTS y API de Gemini
- **Google API Key:** gratuita en [aistudio.google.com](https://aistudio.google.com)

---

## 🚀 Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/parawalter/VentasEnVivo.git
cd VentasEnVivo
```

### 2. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

Las dependencias principales son:

```
flask          # Servidor web interno
flask-cors     # Soporte CORS
requests       # Llamadas HTTP a APIs
python-dotenv  # Carga de variables de entorno
pywebview      # Ventana de escritorio nativa
urllib3        # HTTP utilities
edge-tts       # Síntesis de voz neural Microsoft
```

### 3. Configurar API Key

Crea un archivo `.env` en la raíz del proyecto:

```env
Google-API-KEY=tu_api_key_aqui
```

> 💡 Obtén tu API Key gratuita en: https://aistudio.google.com/apikey

### 4. Agregar Avatares GLB

Coloca tus archivos `.glb` en la carpeta `avatares/`. Los avatares no se incluyen en el repositorio por su tamaño.

**Fuentes recomendadas de avatares:**
- [ReadyPlayerMe](https://readyplayer.me) — avatares personalizables gratis
- [Sketchfab](https://sketchfab.com) — biblioteca 3D (filtrar por `.glb`)

### 5. Iniciar la aplicación

**Con consola** (recomendado para debug):
```bash
run.bat
```

**Sin consola** (producción, doble clic):
```
iniciar.vbs
```

La aplicación se abre automáticamente en `http://127.0.0.1:5000`

---

## 📂 Estructura del proyecto

```
VentasEnVivo/
├── main.py                  # Backend Flask + lógica principal
├── run.bat                  # Script de inicio (CON consola)
├── iniciar.vbs              # Script de inicio (SIN consola)
├── requirements.txt         # Dependencias Python
├── custom_avatars.json      # Metadata de avatares personalizados
├── CAPACIDADES_AVATAR.md    # Documentación de expresiones y gestos
├── .env                     # ⚠️ NO incluido en git (API Keys)
├── .gitignore
│
├── templates/
│   └── index.html           # Frontend completo (HTML + CSS + JS)
│
├── avatares/                # Archivos .glb de avatares (NO incluidos)
│   └── *.glb
│
└── static/
    ├── models/              # Assets 3D adicionales
    └── tts/                 # Audio TTS generado (temporal, ignorado)
```

---

## 🎮 Guía de uso

### Hablar con el avatar

1. Escribe el texto en el campo **"Comunicación Humana"**
2. Presiona **HABLAR AHORA** → el avatar habla con la voz seleccionada

### Mejorar el texto con IA

1. Escribe el texto
2. Presiona **✨ ADAPTAR** → Gemini analiza el texto e inserta expresiones faciales:
   - `(feliz)` `(triste)` `(enojo)` `(sorpresa)` `(guiño)` `(serio)` `(broma)` `(llorar)`
3. El texto adaptado se muestra resaltado en el campo
4. Presiona **HABLAR AHORA**

### Expresiones faciales directas

Haz clic en los emojis del panel derecho para aplicar expresiones instantáneas.

### Controles de cámara

| Control | Función |
|---------|---------|
| **ALTURA** | Sube/baja el punto focal de la cámara |
| **ZOOM** | Acerca o aleja la vista |
| **GIRO Y** | Gira el avatar izquierda/derecha |
| **GIRO X** | Inclina la cámara arriba/abajo |

**Presets de encuadre:**

| Preset | Descripción |
|--------|-------------|
| 🧍 Completo | Cuerpo completo frontal |
| 👙 Cintura | De cintura hacia arriba |
| 👤 Busto | Hombros y cara |
| 😊 Rostro | Primer plano de la cara |
| 🚶 Der. / Izq. | Perfil del cuerpo |
| 🏃 Espalda | Vista posterior |
| 🤸 Cara Der. / Izq. | Perfil del rostro |

> 💡 También puedes rotar el avatar con el **mouse** (clic + arrastrar)

### Verificar la API Key

Presiona **🔍 TEST API GEMINI** para:
- Confirmar que tu key es válida
- Ver todos los modelos Gemini disponibles para tu key

---

## 🔧 Endpoints del servidor interno

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/` | Interfaz principal |
| `POST` | `/hablar` | Hace hablar al avatar con el texto dado |
| `POST` | `/tts` | Genera audio con Edge-TTS |
| `GET` | `/tts-voices` | Lista voces neurales disponibles |
| `POST` | `/adaptar` | Adapta texto con expresiones via Gemini |
| `GET` | `/test-api` | Verifica API Key y lista modelos |
| `GET` | `/avatars` | Lista avatares disponibles en disco |
| `GET` | `/avatares/<file>` | Sirve archivos GLB |
| `POST` | `/log` | Registro de eventos del frontend |

---

## 🧠 Integración con Google Gemini

El endpoint `/adaptar` usa **auto-descubrimiento de modelos**:

1. Consulta `GET /v1beta/models` con tu API Key
2. Filtra modelos que soporten `generateContent` (excluye imagen/embedding)
3. Ordena por velocidad: `flash-lite` → `flash` → `pro`
4. Prueba modelos en orden hasta encontrar uno disponible

Esto garantiza compatibilidad con **cualquier tipo de API Key**, incluso las que tienen acceso a modelos nuevos como `gemini-2.5-flash-lite` o `gemini-3-flash-preview`.

---

## 🛡️ Seguridad

- La **API Key** se almacena únicamente en `.env` (nunca en el código)
- `.env` está excluido de git via `.gitignore`
- Las llamadas a la API usan `verify=False` para compatibilidad con proxies SSL corporativos
- La aplicación solo es accesible desde `localhost` (no expuesta a la red)

---

## 🐛 Solución de problemas

| Problema | Solución |
|----------|---------|
| La app no abre | Verifica que el puerto 5000 está libre. Cierra instancias previas. |
| Avatar no habla | Revisa conexión a internet (Edge-TTS requiere red) |
| ADAPTAR no funciona | Usa **🔍 TEST API** para diagnosticar la API Key |
| "Ningún modelo disponible" | Tu key podría tener modelos distintos. TEST API te dice cuáles tienes. |
| Zapatos en primer plano | Ajusta manualmente el slider ALTURA a ~1.5 para encuadre de rostro |
| Error SSL/Proxy | Normal en redes corporativas. `verify=False` ya está configurado. |

---

## 📋 Changelog

### v3.0.0 — 2026-02-20
- ✅ Auto-descubrimiento de modelos Gemini (compatible con cualquier API Key)
- ✅ Botón TEST API GEMINI con modal de diagnóstico
- ✅ Dos sliders de giro independientes: Eje Y (izq/der) y Eje X (arriba/abajo)
- ✅ ALTURA usa `controls.target.y` (compatible con OrbitControls)
- ✅ Presets de cámara recalibrados para el nuevo sistema de altura
- ✅ Expresiones ampliadas: `(broma)` y `(llorar)`
- ✅ Al cerrar la ventana del avatar, se cierra toda la app (`os._exit(0)`)
- ✅ Instancia única garantizada por socket en puerto 5000

### v2.0.0 — 2026-02-18
- ✅ Sistema de URLs de avatar guardadas
- ✅ Fix: pantalla en blanco con avatar "Sofia"
- ✅ Zoom extendido para ver el avatar completo

### v1.0.0 — 2026-02-17
- ✅ Lanzamiento inicial con D-ID avatar
- ✅ Voz neural Edge-TTS
- ✅ Panel de control completo

---

## 👨‍💻 Autor

**Ing. Walter Rodríguez**  
Desarrollado con Python, Flask, Three.js y TalkingHead

---

## 📄 Licencia

Uso privado — Todos los derechos reservados © 2026
