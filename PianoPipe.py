import math
from typing import NamedTuple

import cv2
import mediapipe as mp
import numpy as np
import pygame


SAMPLE_RATE = 44100
NOTE_DURATION = 0.35

# Puntos de la palma usados para calcular el centro de la mano
PALM_CENTER_LANDMARKS = (0, 5, 9, 13, 17)

# --- Ajustes de deteccion (todo relativo al tamano de la mano) ---
# Un dedo "toca" la palma cuando su yema entra a este radio (en multiplos
# del tamano de la mano: distancia muneca -> base del dedo medio).
ENTER_RADIUS = 0.45
# Para soltar, la yema debe salir de un radio mayor (histeresis anti-parpadeo)
EXIT_RADIUS = 0.65
DEBOUNCE_FRAMES = 2

START_OCTAVE = 5

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
BLACK_NOTE_SEMITONES = frozenset((1, 3, 6, 8, 10))


class FingerKey(NamedTuple):
    side: str
    finger: str
    tip_landmark: int
    semitone: int   # semitonos sobre C
    label: str


# De izquierda a derecha se sigue el orden del teclado: C D D# E F G A A# B C.
# Las ocho notas naturales quedan en orden ascendente; D# y A# son teclas negras.
FINGER_KEYS = (
    FingerKey("left", "pinky", 20, 0, "IZQ-ME"),
    FingerKey("left", "ring", 16, 2, "IZQ-A"),
    FingerKey("left", "middle", 12, 3, "IZQ-M (D#)"),
    FingerKey("left", "index", 8, 4, "IZQ-I"),
    FingerKey("left", "thumb", 4, 5, "IZQ-PU"),
    FingerKey("right", "thumb", 4, 7, "DER-PU"),
    FingerKey("right", "index", 8, 9, "DER-I"),
    FingerKey("right", "middle", 12, 10, "DER-M (A#)"),
    FingerKey("right", "ring", 16, 11, "DER-A"),
    FingerKey("right", "pinky", 20, 12, "DER-ME"),
)

# Jingle Bells transpuesta de Do mayor a Sib mayor para usar D# (Mib) y A# (Sib).
JINGLE_BELLS = (
    "D D D D D D D F A# C D "
    "D# D# D# D# D# D D D D D C C D C F "
    "D D D D D D D F A# C D "
    "D# D# D# D# D# D D D D F F D# C A#"
).split()

# Para cada letra de nota, el dedo que la toca (la primera coincidencia)
NOTE_TO_KEY = {}
for _key in FINGER_KEYS:
    NOTE_TO_KEY.setdefault(NOTE_NAMES[_key.semitone % 12], _key)


def midi_for(octave, semitone):
    return 12 * (octave + 1) + semitone


def frequency_for(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def note_label(midi):
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def make_tone(frequency):
    """Crea un tono corto con fundido suave para el mezclador de pygame."""
    mixer_settings = pygame.mixer.get_init()
    if mixer_settings is None:
        raise RuntimeError("El mezclador de audio no esta inicializado.")
    sample_rate, sample_format, channels = mixer_settings
    if sample_format != -16:
        raise RuntimeError("El mezclador debe usar audio PCM de 16 bits.")

    count = int(sample_rate * NOTE_DURATION)
    index = np.arange(count)
    fade_in = np.minimum(1.0, index / (sample_rate * 0.015))
    fade_out = np.minimum(1.0, (count - index) / (sample_rate * 0.06))
    envelope = np.minimum(fade_in, fade_out)
    wave = 9000 * envelope * np.sin(2 * np.pi * frequency * index / sample_rate)
    samples = wave.astype(np.int16)
    if channels > 1:
        samples = np.repeat(samples[:, None], channels, axis=1)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def build_sounds():
    """Pre-genera todos los tonos posibles para evitar retrasos al tocar."""
    sounds = {}
    for key in FINGER_KEYS:
        midi = midi_for(START_OCTAVE, key.semitone)
        if midi not in sounds:
            sounds[midi] = make_tone(frequency_for(midi))
    return sounds


def assign_sides(handedness, centers_x):
    """Decide cual mano es izquierda/derecha.

    Usa la etiqueta de MediaPipe; si hay conflicto (dos manos con la misma
    etiqueta) o no hay etiqueta, usa la posicion en pantalla.
    """
    labels = []
    for index in range(len(centers_x)):
        label = None
        if index < len(handedness) and handedness[index].classification:
            candidate = handedness[index].classification[0].label.lower()
            if candidate in ("left", "right"):
                label = candidate
        labels.append(label)

    if len(labels) == 2 and (labels[0] is None or labels[0] == labels[1]):
        left_first = centers_x[0] < centers_x[1]
        return ["left", "right"] if left_first else ["right", "left"]

    return [
        label if label else ("left" if centers_x[i] < 0.5 else "right")
        for i, label in enumerate(labels)
    ]


def get_hand_geometry(hand_landmarks, frame_width, frame_height):
    points = [
        (landmark.x * frame_width, landmark.y * frame_height)
        for landmark in hand_landmarks.landmark
    ]
    cx = sum(points[i][0] for i in PALM_CENTER_LANDMARKS) / len(PALM_CENTER_LANDMARKS)
    cy = sum(points[i][1] for i in PALM_CENTER_LANDMARKS) / len(PALM_CENTER_LANDMARKS)
    size = max(math.dist(points[0], points[9]), 1.0)
    return points, (cx, cy), size


def draw_keyboard(frame, active_keys, octave):
    frame_height, frame_width = frame.shape[:2]
    margin = 18
    top = frame_height - 105
    key_width = (frame_width - 2 * margin) // len(FINGER_KEYS)

    for index, key in enumerate(FINGER_KEYS):
        x1 = margin + index * key_width
        x2 = x1 + key_width
        pressed = (key.side, key.finger) in active_keys

        is_black_key = key.semitone % 12 in BLACK_NOTE_SEMITONES
        base = (55, 55, 55) if is_black_key else (235, 235, 235)
        text_color = (245, 245, 245) if is_black_key else (20, 20, 20)
        title = note_label(midi_for(octave, key.semitone))

        color = (70, 210, 120) if pressed else base
        cv2.rectangle(frame, (x1, top), (x2, frame_height - 15), color, -1)
        cv2.rectangle(frame, (x1, top), (x2, frame_height - 15), (40, 40, 40), 2)
        cv2.putText(frame, title, (x1 + 5, top + 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, text_color, 2)
        cv2.putText(frame, key.label, (x1 + 3, top + 65),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, text_color, 1)


def draw_guide(frame, step, finished_timer):
    """Panel superior con las proximas notas de Jingle Bells."""
    frame_width = frame.shape[1]
    panel_height = 98

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame_width, panel_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    title = f"Jingle Bells - Sib mayor  ({min(step + 1, len(JINGLE_BELLS))}/{len(JINGLE_BELLS)})"
    if finished_timer > 0:
        title = "Terminaste la cancion!"
    cv2.putText(frame, title, (18, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    visible = JINGLE_BELLS[step:step + 8]
    margin = 18
    box_width = (frame_width - 2 * margin) // 8
    for i, letter in enumerate(visible):
        x1 = margin + i * box_width
        x2 = x1 + box_width - 6
        current = i == 0
        fill = (60, 220, 255) if current else (210, 210, 210)
        cv2.rectangle(frame, (x1, 32), (x2, 90), fill, -1)
        cv2.rectangle(frame, (x1, 32), (x2, 90), (30, 30, 30), 2)
        cv2.putText(frame, letter, (x1 + 8, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (20, 20, 20), 2)
        cv2.putText(frame, NOTE_TO_KEY[letter].label, (x1 + 4, 83),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (30, 30, 30), 1)


def main():
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
    pygame.mixer.set_num_channels(16)
    sounds = build_sounds()

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        camera.release()
        hands.close()
        pygame.mixer.quit()
        raise RuntimeError("No se pudo abrir la camara web (indice 0).")

    octave = START_OCTAVE
    streaks = {}           # (side, finger) -> frames consecutivos tocando
    active_keys = set()    # teclas actualmente presionadas
    guide_on = False
    guide_step = 0
    finished_timer = 0

    print("Piano iniciado. Dobla cada dedo hasta tocar la palma de SU misma mano.")
    print("Octava fija: 5. Los meniques tocan C5 y C6; D# y A# son teclas negras.")
    print("Presiona 'g' para mostrar/ocultar la guia.")
    print("Presiona 'q' para salir.")

    def toggle_guide():
        nonlocal guide_on, guide_step, finished_timer
        guide_on = not guide_on
        guide_step = 0
        finished_timer = 0

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("No se pudo leer un fotograma de la camara.")
                break

            frame = cv2.flip(frame, 1)
            frame_height, frame_width = frame.shape[:2]
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            detected = results.multi_hand_landmarks or []
            handedness = results.multi_handedness or []

            geometries = [
                get_hand_geometry(h, frame_width, frame_height) for h in detected
            ]
            sides = assign_sides(
                handedness, [g[1][0] / frame_width for g in geometries]
            )
            hands_by_side = {
                side: geometry for side, geometry in zip(sides, geometries)
            }

            for hand_landmarks, (points, center, size) in zip(detected, geometries):
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
                cv2.circle(
                    frame, (int(center[0]), int(center[1])),
                    int(ENTER_RADIUS * size), (255, 170, 40), 2,
                )

            # --- Deteccion: cada dedo contra la palma de SU misma mano ---
            new_active = set()
            for key in FINGER_KEYS:
                key_id = (key.side, key.finger)
                geometry = hands_by_side.get(key.side)
                inside = False
                if geometry is not None:
                    points, center, size = geometry
                    distance = math.dist(points[key.tip_landmark], center) / size
                    threshold = EXIT_RADIUS if key_id in active_keys else ENTER_RADIUS
                    inside = distance < threshold

                streaks[key_id] = streaks.get(key_id, 0) + 1 if inside else 0

                if streaks[key_id] >= DEBOUNCE_FRAMES:
                    new_active.add(key_id)
                    if key_id not in active_keys:  # flanco de subida: evento
                        midi = midi_for(octave, key.semitone)
                        sounds[midi].play()
                        letter = NOTE_NAMES[key.semitone % 12]
                        if guide_on and guide_step < len(JINGLE_BELLS):
                            if letter == JINGLE_BELLS[guide_step]:
                                guide_step += 1
                                if guide_step >= len(JINGLE_BELLS):
                                    guide_step = 0
                                    finished_timer = 90
            active_keys = new_active

            # --- Dibujo ---
            if finished_timer > 0:
                finished_timer -= 1

            text_y = 125 if guide_on else 32
            cv2.putText(
                frame,
                f"Manos: {len(detected)}/2   Octava: {octave}",
                (18, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (40, 230, 40), 2,
            )
            cv2.putText(
                frame,
                "Dobla un dedo hasta tocar la palma de su misma mano",
                (18, text_y + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2,
            )
            if guide_on:
                draw_guide(frame, guide_step, finished_timer)
            draw_keyboard(frame, active_keys, octave)
            cv2.imshow("Piano con las manos", frame)

            key_pressed = cv2.waitKey(1) & 0xFF
            if key_pressed == ord("q"):
                break
            if key_pressed == ord("g"):
                toggle_guide()
    finally:
        camera.release()
        hands.close()
        cv2.destroyAllWindows()
        pygame.mixer.quit()


if __name__ == "__main__":
    main()