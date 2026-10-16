import cv2
import mediapipe as mp

#Codigo creado por Gemini para la experimentacion y prueba de la deteccion de manos con MediaPipe y OpenCV

# Inicializar los módulos de MediaPipe para detección de manos
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Configurar el objeto Hands con parámetros iniciales
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # Número máximo de manos a detectar
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# Abrir la cámara web por defecto (índice 0)
cap = cv2.VideoCapture(0)

print("Cámara iniciada. Muestra tus manos frente a ella. Presiona 'q' para salir.")

while cap.isOpened():
  success, frame = cap.read()
  if not success:
    print("No se pudo acceder a la cámara.")
    break

  # Voltear la imagen horizontalmente (efecto espejo) y convertir de BGR a RGB
  frame = cv2.flip(frame, 1)
  rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

  # Procesar la imagen para buscar manos con MediaPipe
  results = hands.process(rgb_frame)

  # Si se detectan manos, dibujar las conexiones y puntos articulares (esios esqueletos virtuales)
  if results.multi_hand_landmarks:
    for hand_landmarks in results.multi_hand_landmarks:
      mp_drawing.draw_landmarks(
          frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
      )

  # Mostrar la ventana con el resultado en tiempo real
  cv2.imshow("Seguimiento de Manos con MediaPipe", frame)

  # Romper el bucle si el usuario presiona la tecla 'q'
  if cv2.waitKey(1) & 0xFF == ord("q"):
    break

# Liberar la cámara y cerrar todas las ventanas de OpenCV
cap.release()
cv2.destroyAllWindows()