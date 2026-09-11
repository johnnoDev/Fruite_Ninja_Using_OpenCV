# Fruit Ninja - Controlado con la Mano (IA)

Un juego de visión por computadora de alto rendimiento donde juegas Fruit Ninja usando tu mano real como la hoja. Construido con Python, OpenCV, MediaPipe y Pygame.

## Características

* **Seguimiento de mano en tiempo real**: usa MediaPipe (API Tasks / `HandLandmarker`) para rastrear la punta de tu dedo índice con baja latencia y suavizado adaptativo.
* **Reconocimiento de gestos**: detecta **Palma Abierta**, **Puño** y **Seña de Paz** a partir de la extensión de los dedos.
* **Dos formas de control**: juega con la **mano** (cámara web) o con el **ratón**, elegible desde el menú.
* **Recorte de fondo (solo modo mano)**: mientras juegas con la cámara, tu silueta se recorta en tiempo real (segmentación selfie de MediaPipe) y se muestra sobre el fondo del juego en vez del video crudo de la webcam.
* **Física de juego**: las frutas y bombas se lanzan y caen con gravedad; la colisión de la hoja usa detección de segmento de línea (cápsula) para cortes rápidos y precisos.
* **Efectos visuales**:
    * **Estela de la hoja**: rastro cian dinámico que sigue tu dedo, con grosor y desvanecimiento variables.
    * **Frutas reales**: assets de manzana, plátano, coco, naranja, piña y sandía, cada una con su versión partida en dos mitades.
    * **Salpicaduras y explosiones**: efecto de jugo al cortar fruta y explosión animada al detonar una bomba, con vibración de pantalla.
* **Dos modos de juego**:
    * **Clásico**: comienzas con 3 vidas; una bomba o una fruta perdida te quita una vida.
    * **Supervivencia**: 1 sola vida; una bomba o una fruta perdida termina la partida al instante.
* **Bombas**: evita cortar las bombas oscuras con mecha; te cuestan una vida (o la partida en Supervivencia).
* **Pausa de palma**: muestra la **Palma Abierta** a la cámara para congelar el corte sin pausar el menú (mecanismo de seguridad).
* **Power-ups por gesto**: sostén una pose durante ~0.25s para activarla; luego entra en tiempo de reenfriamiento:
    * **Puño → Escudo**: absorbe la próxima bomba que golpees, sin perder vida.
    * **Seña de Paz (índice + medio) → Cámara Lenta**: las frutas y bombas caen en cámara lenta durante unos segundos.
    * En modo ratón, estos power-ups se activan con **Clic Derecho** (Escudo) y **Clic Central** (Cámara Lenta).
* **Menú de pausa**: presiona `ESC` durante la partida para pausar, reanudar o volver al menú.
* **Sistema de puntuación y vidas**: se muestran en pantalla junto con el estado de cada power-up (activo / en recarga / listo).
* **Audio completo**: música de fondo distinta para menú y partida (con variante más rápida en Cámara Lenta), y efectos de sonido para cortes, combos, bombas, inicio y fin de juego.

## Estructura del proyecto

```
Fruite_Ninja_Using_OpenCV/
├── main.py            # Bucle principal, manejo de escenas y lógica de la partida
├── game_engine.py      # Modos de juego: GameMode, ClassicMode, SurvivalMode
├── game_objects.py     # Blade (hoja), Fruit, SlicedFruit, Bomb, Explosion, SplashEffect
├── input_manager.py    # Proveedores de entrada: MouseInput y HandInput
├── sensors.py           # HandTracker, WebcamStream y BackgroundRemover (MediaPipe Tasks API)
├── ui_manager.py        # SceneManager y botones de la interfaz (menús, pausa, fin de juego)
├── audio_manager.py     # Carga y reproducción de música y efectos de sonido
├── physics.py           # Colisión de cápsula (segmento de línea) contra círculo
├── hand_tracker.py      # Rastreador de mano alternativo (API clásica mediapipe.solutions, no usado por main.py)
├── convert_audio.py     # Utilidad para convertir audios .m4a a .wav
├── requirements.txt      # Dependencias del proyecto
└── assets/               # Imágenes, sonidos y modelos (frutas, vfx, audio, fondos, modelos de IA)
```

## Requisitos previos

* Python 3.9 - 3.14
* Cámara web (solo necesaria si eliges jugar con la mano)

## Instalación

1. Clona el repositorio (o descarga los archivos).
2. Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    venv\Scripts\activate        # Windows  (usa: source venv/bin/activate en Linux/Mac)
    pip install -r requirements.txt
    ```

> En la primera ejecución el juego descarga automáticamente los modelos de MediaPipe:
> el modelo de seguimiento de manos (~7 MB) y el de segmentación selfie (~250 KB),
> ambos guardados en `assets/models/`. Se necesita conexión a internet solo esa vez.

### Nota sobre Python 3.13 / 3.14

La API clásica `mediapipe.solutions` no tiene wheels para Python 3.13+, así que el
seguimiento de manos usa la más reciente **API de MediaPipe Tasks** (`HandLandmarker`).
El juego también usa `pygame-ce` (una réplica compatible de `pygame` que sí distribuye
wheels para 3.14).

## Cómo jugar

1. Ejecuta el juego:
    ```bash
    python main.py
    ```
2. En el menú, selecciona **Jugar → un modo (Clásico o Supervivencia) → un control (Ratón o Cámara)**.
3. **Controles con la mano**:
    * **Cortar**: mueve tu dedo índice por la pantalla para cortar frutas; debes moverlo con suficiente velocidad para que cuente como corte.
    * **Pausar el corte**: abre la mano (extiende los 5 dedos) para congelar la hoja. Útil si hay una bomba en el camino y quieres mover la mano con seguridad.
    * **Escudo**: cierra el puño para armar un escudo que absorbe tu próximo golpe de bomba.
    * **Cámara Lenta**: haz una seña de paz (índice + medio) para ralentizar la caída de frutas y bombas durante unos segundos.
4. **Controles con el ratón**:
    * **Cortar**: mantén presionado el **clic izquierdo** y arrastra el ratón.
    * **Escudo**: mantén presionado el **clic derecho**.
    * **Cámara Lenta**: mantén presionado el **clic central**.
5. **Pausar la partida**: presiona `ESC`.
6. **Salir**: cierra la ventana o presiona `Alt+F4`.

## Solución de problemas

* **¿Hay retraso (lag)?** Asegúrate de tener buena iluminación frente a la cámara.
* **¿Error de cámara?** El código usa `cv2.CAP_DSHOW` para compatibilidad con Windows. En Linux/Mac es posible que debas quitar esa opción en `sensors.py`.
* **¿La descarga del modelo falla?** Verifica tu conexión a internet; los modelos se descargan una sola vez en `assets/models/` y luego quedan en caché localmente.

## Créditos

Construido con:
* [MediaPipe](https://developers.google.com/mediapipe)
* [Pygame](https://www.pygame.org/)
* [OpenCV](https://opencv.org/)
