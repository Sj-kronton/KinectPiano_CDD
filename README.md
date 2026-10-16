# Piano virtual controlado con las manos
## Juan Alejandro Sierra Rincon - U00178520

Aplicación en Python que utiliza la cámara web para detectar los dedos y convertir sus gestos en notas musicales. Incluye un teclado virtual de diez notas y una guía interactiva para tocar **Jingle Bells**.

## Características

- Detecta hasta dos manos mediante MediaPipe.
- Cada tecla se activa al doblar el dedo correspondiente hacia la palma de esa mano (indicado por circulo azul).
- Genera tonos de audio en tiempo real con Pygame.
- Muestra en pantalla las manos detectadas, las teclas y la octava.
- Incluye una guía de notas para **Jingle Bells**, transpuesta a Sib mayor (Acticada con 'G').
- No requiere un teclado físico ni archivos de audio externos.

## Mapeo de dedos y notas

El teclado se presenta de izquierda a derecha en orden cromático. Las ocho notas naturales están en orden ascendente; Re# y La# representan dos teclas negras.

| Posición | Mano | Dedo | Nota |
|---:|---|---|---|
| 1 | Izquierda | Meñique | Do5 (C5) |
| 2 | Izquierda | Anular | Re5 (D5) |
| 3 | Izquierda | Medio | Re#5 / Mib5 (D#5 / Eb5) |
| 4 | Izquierda | Índice | Mi5 (E5) |
| 5 | Izquierda | Pulgar | Fa5 (F5) |
| 6 | Derecha | Pulgar | Sol5 (G5) |
| 7 | Derecha | Índice | La5 (A5) |
| 8 | Derecha | Medio | La#5 / Sib5 (A#5 / Bb5) |
| 9 | Derecha | Anular | Si5 (B5) |
| 10 | Derecha | Meñique | Do6 (C6) |

La octava inicial es 5. Es fija

## Requisitos

- Python 3.11.9
- Cámara web
- Salida de audio
- Paquetes de Python:
  - OpenCV (`opencv-python`)
  - MediaPipe (`mediapipe`)
  - NumPy (`numpy`)
  - Pygame (`pygame`)

## Instalación

Desde la raíz del repositorio, instala las dependencias:

```bash
python -m pip install opencv-python mediapipe numpy pygame
```

## Ejecución

Desde la raíz del repositorio:

```bash
python Trabajo_Piano/PianoPipe.py
```

O desde esta carpeta:

```bash
python PianoPipe.py
```

Al iniciar, permite el acceso a la cámara y asegúrate de que el dispositivo de audio esté disponible.

## Controles

- **Doblar un dedo:** tocar la nota asignada. La yema debe acercarse a la palma de la misma mano.
- **`g`:** mostrar u ocultar la guía de Jingle Bells.
- **`q`:** salir.

La guía comienza desde la primera nota cada vez que se activa. Las notas incorrectas suenan, pero no avanzan la secuencia.

## Detección de gestos

La aplicación calcula el centro de la palma a partir de puntos de referencia de la mano y mide la distancia de cada yema con respecto a ese centro. La distancia se normaliza según el tamaño de la mano para que la detección dependa menos de cuánto ocupa la mano en la imagen. Se utilizan umbrales distintos para activar y soltar una nota, además de una breve confirmación de varios fotogramas, para reducir activaciones intermitentes.

La identificación de las manos usa la clasificación de MediaPipe y recurre a su posición en la imagen si las etiquetas faltan o entran en conflicto. La cámara utilizada es la de índice `0`.

## Guía de Jingle Bells

La guía usa las notas **Do, Re, Re#, Fa, Sol y La#**. Corresponde a una transposición de dos semitonos hacia abajo respecto a la versión en Do mayor: las notas originales Mi y Fa pasan a Re y Re#, y Do pasa a La#. Así la melodía utiliza las dos teclas negras disponibles, Re# y La#.

## Origen y evolución observable

En esta carpeta se conserva `PruebasPipe.py`, un prototipo que abre la cámara y dibuja los puntos y conexiones de las manos detectadas. `PianoPipe.py` amplía esa prueba con detección de gestos para tocar notas, síntesis de audio, visualización de un teclado y una guía musical.


## Solución de problemas

- **No se abre la cámara:** comprueba que esté conectada y que ninguna otra aplicación la esté usando. El script intenta abrir el dispositivo con índice `0`.
- **No se escucha audio:** comprueba la salida de audio del sistema y que Pygame pueda inicializar el mezclador.
- **No se detectan bien los dedos:** coloca ambas manos dentro del encuadre, con la palma visible, y dobla un dedo cada vez hacia la palma de su misma mano.
- **Falta un paquete:** vuelve a ejecutar el comando de instalación de dependencias en el mismo entorno de Python con el que inicias el programa.

# Se asistio a la conferencia de Cotrans
