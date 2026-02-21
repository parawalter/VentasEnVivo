# Documentación Técnica: Capacidades del Avatar (TalkingHead + ReadyPlayerMe)

Esta documentación detalla las capacidades técnicas del sistema de avatares implementado, basado en la librería `TalkingHead` (frontend) y modelos GLB v2 de `ReadyPlayerMe`.

## 1. Control de Expresiones (Emociones)

El avatar soporta cambios de estado de ánimo mediante la manipulación de **Morph Targets** (blendshapes) del modelo 3D.

### API de Frontend (`TeachingHead`)
- **Método Principal**: `head.speakEmoji(emoji)`
- **Funcionamiento**: Recibe un emoji (string) y activa una combinación predefinida de morph targets para simular la emoción.

### Mapeo de Expresiones Soportadas
El sistema actual mapea etiquetas de texto a los siguientes emojis/estados:

| Etiqueta (Comando) | Emoji | Descripción Técnica (Morph Targets Afectados) |
| Etiqueta (Comando) | Emoji | Descripción Técnica (Morph Targets Afectados) |
| :--- | :--- | :--- |
| `(feliz)`, `(contento)`, `(happy)`, `(joy)` | 😊 | `mouthSmile`, `eyesClosed` (parcial), elevación de mejillas. |
| `(triste)`, `(sad)` | 😞 | `mouthFrown`, `browDownLeft/Right`. |
| `(llorar)`, `(cry)` | 😭 | `mouthFrown` intenso, `eyesClosed` intermitente. |
| `(sorpresa)`, `(asombrado)`, `(surprise)`, `(shock)` | 😮 | `mouthOpen`, `browInnerUp`, ojos muy abiertos. |
| `(enojo)`, `(molesto)`, `(angry)`, `(mad)` | 😠 | `browDownLeft/Right`, `mouthFrown`. |
| `(guiño)`, `(wink)` | 😉 | `eyeBlinkLeft` (o Right) al 100%, media sonrisa. |
| `(serio)`, `(serious)` | 😐 | Reset de todos los targets emocionales a 0 (Neutral). |
| `(broma)`, `(joke)` | 😜 | Guiño + sacar lengua (si el modelo tiene `tongueOut`, sino sonrisa pícara). |

**Nota**: Estas expresiones se activan automáticamente al incluir la etiqueta en el texto a hablar (en Español o Inglés). La etiqueta se elimina del audio pero dispara la animación.

---

## 2. Animación de Labios (Lip-Sync)

El sistema utiliza una sincronización labial basada en **Visemas Oculus OVR** estándar.

### Funcionamiento Técnico
1.  **Audio**: Se genera un archivo MP3 mediante Edge-TTS en el backend.
2.  **Sincronización**: El frontend calcula la posición del audio en tiempo real (`audio.currentTime`).
3.  **Mapeo Texto-Visema**: Se analiza el carácter de texto correspondiente al tiempo actual y se mapea a un visema OVR.
4.  **Inyección**: Se inyecta el valor del visema directamente en las mallas (`meshes`) del avatar.

### Visemas Soportados (Oculus Standard)
El modelo GLB debe incluir los siguientes Morph Targets para hablar correctamente:

| Visema (Nombre Técnico) | Fonemas/Sonidos | Descripción Visual |
| :--- | :--- | :--- |
| `viseme_aa` | /a/ | Boca muy abierta. |
| `viseme_E` | /e/ | Boca medio abierta, comisuras estiradas. |
| `viseme_I` | /i/ | Boca casi cerrada, sonrisa amplia. |
| `viseme_O` | /o/ | Labios redondeados. |
| `viseme_U` | /u/ | Labios muy fruncidos hacia afuera. |
| `viseme_PP` | /p/, /b/, /m/ | Labios cerrados y apretados. |
| `viseme_FF` | /f/, /v/ | Diente superior toca labio inferior. |
| `viseme_TH` | /th/ | Lengua entre dientes (si soportado). |
| `viseme_DD` | /t/, /d/ | Boca entreabierta, lengua arriba. |
| `viseme_kk` | /k/, /g/ | Boca abierta, garganta activa (visual boca media). |
| `viseme_nn` | /n/ | Similar a DD pero más cerrado. |
| `viseme_RR` | /r/, /l/ | Boca en forma de caja neutral. |
| `viseme_SS` | /s/, /z/ | Dientes juntos, labios separados. |
| `viseme_CH` | /ch/, /j/, /sh/ | Labios proyectados (trompa). |
| `viseme_sil` | (Silencio) | Boca en reposo (Neutral). |

---

## 3. Movimientos Corporales y Cabeza

El avatar cuenta con un sistema de **Idle Animation** (Movimiento en reposo) y seguimiento básico.

- **Respiración**: Animación procedimental que escala ligeramente el pecho/torso.
- **Micro-movimientos**: La cabeza oscila sutilmente para evitar parecer estática.
- **Parpadeo (Blinking)**: Automático. Usa `eyesClosed` o `eyeBlinkLeft/Right` de forma aleatoria cada 2-5 segundos.
- **LookAt (Mirada)**: El avatar está configurado para mirar a la cámara (`camera`) por defecto.

---

## 4. Control de Cámara (Viewport)

Permite manipular cómo el usuario ve al avatar.

### Parámetros Controlables
1.  **Altura (Y)**:
    *   Rango: `-1` (Pies) a `2` (Sobre la cabeza).
    *   Uso: Permite encuadrar desde primer plano (cara) hasta cuerpo completo.
2.  **Zoom (Z/Distance)**:
    *   Rango: `0.2` (Muy cerca) a `10` (Muy lejos).
    *   Uso: Escala aparente del avatar.
3.  **Rotación (Y-Axis)**:
    *   Rango: `-3.14` (-180°) a `3.14` (180°).
    *   Uso: Permite girar al avatar para verlo de perfil o espalda.

---

## 5. Requisitos del Modelo 3D (.glb)

Para que un avatar personalizado funcione el 100% de las capacidades descritas, debe cumplir:

1.  **Formato**: `.glb` (glTF binario).
2.  **Esqueleto (Rig)**: Estándar humanoide compatible con Mixamo/RPM.
3.  **Morph Targets (Blendshapes)**:
    *   Debe incluir el set **ARKit** (para expresiones faciales ricas).
    *   Debe incluir el set **Oculus Visemes** (para lip-sync preciso).
    *   Se recomienda añadir el parámetro `?morphTargets=ARKit,Oculus+Visemes` a la URL de ReadyPlayerMe al descargar.

## 6. Integración (API Interna)

Si deseas controlar el avatar programáticamente desde la consola o scripts externos, expone estas funciones globales en `.index.html`:

- `handleSpeak()`: Lee el texto del input, procesa etiquetas y habla.
- `addExpression(tag)`: Inserta una etiqueta de emoción en el texto.
- `updateCamera()`: Aplica los valores de los sliders de cámara.
- `loadAvatar(url)`: Carga un nuevo modelo GLB en caliente.
