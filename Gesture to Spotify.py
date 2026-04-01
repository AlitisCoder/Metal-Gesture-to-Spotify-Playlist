import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import webbrowser
import time
import urllib.request
import os

# Spotify Playlist
SPOTIFY_URL = "https://open.spotify.com/playlist/2pUqkWhPN35vwvIG2QSVnl"

HOLD_FRAMES_REQUIRED = 20
COOLDOWN_SECONDS = 5 
MODEL_PATH = "hand_landmarker.task"

# Modell automatisch herunterladen falls nicht vorhanden
if not os.path.exists(MODEL_PATH):
    print("Lade Hand-Modell herunter (~8MB)...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
        "hand_landmarker/float16/1/hand_landmarker.task",
        MODEL_PATH
    )
    print("Modell bereit!")


def draw_landmarks(frame, landmarks):
    # Verbindungen zwischen Hand-Punkten zeichnen
    h, w = frame.shape[:2]
    connections = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),(0,17)
    ]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in connections:
        cv2.line(frame, pts[a], pts[b], (0, 200, 255), 2)
    for x, y in pts:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)


def is_metal_sign(landmarks):
    """
    Metal-sign:
      - Zeigefinger  (8)  -> gestreckt
      - Mittelfinger (12) -> eingeklappt
      - Ringfinger   (16) -> eingeklappt
      - Kleinfinger  (20) -> gestreckt
    """
    def up(tip, pip):
        return landmarks[tip].y < landmarks[pip].y

    def down(tip, pip):
        return landmarks[tip].y > landmarks[pip].y

    return up(8, 6) and down(12, 10) and down(16, 14) and up(20, 18)


base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.75,
    min_hand_presence_confidence=0.75,
    min_tracking_confidence=0.75
)

cap = cv2.VideoCapture(0)
hold_counter = 0
last_trigger_time = 0
triggered = False

with vision.HandLandmarker.create_from_options(options) as landmarker:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        timestamp_ms = int(time.time() * 1000)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        metal_detected = False
        now = time.time()
        cooldown_active = (now - last_trigger_time) < COOLDOWN_SECONDS

        if result.hand_landmarks:
            landmarks = result.hand_landmarks[0]
            draw_landmarks(frame, landmarks)

            if is_metal_sign(landmarks):
                metal_detected = True

        # Hold-Zähler
        if metal_detected and not cooldown_active:
            hold_counter += 1
        else:
            hold_counter = max(0, hold_counter - 2)

        # Fortschrittsbalken
        progress = min(hold_counter / HOLD_FRAMES_REQUIRED, 1.0)
        bar_width = int(progress * 300)
        bar_color = (0, 255, 100) if not cooldown_active else (100, 100, 100)

        cv2.rectangle(frame, (10, 30), (310, 55), (40, 40, 40), -1)
        if bar_width > 0:
            cv2.rectangle(frame, (10, 30), (10 + bar_width, 55), bar_color, -1)
        cv2.rectangle(frame, (10, 30), (310, 55), (200, 200, 200), 1)

        # Ausloesen
        if hold_counter >= HOLD_FRAMES_REQUIRED and not cooldown_active:
            webbrowser.open(SPOTIFY_URL)
            last_trigger_time = now
            hold_counter = 0
            triggered = True

        # Status-Text
        if cooldown_active:
            remaining = COOLDOWN_SECONDS - (now - last_trigger_time)
            label = f"Cooldown... {remaining:.1f}s"
            color = (100, 200, 255)
        elif metal_detected:
            label = f"Halte die Geste! ({hold_counter}/{HOLD_FRAMES_REQUIRED})"
            color = (0, 255, 100)
        else:
            label = "Zeige das Metal-Zeichen"
            color = (200, 200, 200)

        cv2.putText(frame, label, (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        if triggered and cooldown_active:
            cv2.putText(frame, "Spotify gestartet!", (60, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 100), 3)

        cv2.imshow("Metal Gesture -> Spotify  |  ESC = Beenden", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()