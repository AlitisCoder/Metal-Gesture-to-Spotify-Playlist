import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import webbrowser as web
import math
import random
import sys
import os


def resource_path(filename):
    """Returns the absolute path to a resource — works both in dev and when packaged with PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


MODEL_PATH = resource_path("hand_landmarker.task")
URL = "https://open.spotify.com/intl-de/track/5UWwZ5lm5PKu6eKsHAGxOk"
IMAGE_PATH = resource_path("herz.jpg")
HOLD_FRAMES_REQUIRED = 20
COOLDOWN_SECONDS = 5

popup_image = cv2.imread(IMAGE_PATH)
if popup_image is None:
    raise FileNotFoundError(f"Bild nicht gefunden: {IMAGE_PATH}")

IMAGE_PATHS = [
    resource_path("meinBromeinTwin.jpg"),
    resource_path("Stalin.PNG"),
    resource_path("Leckermaul.jpeg"),
    resource_path("pic.JPG"),
    resource_path("up.jpg"),
]

RecepBild = resource_path("goat.jpg")


def draw_landmarks(frame, landmarks):
    h, w = frame.shape[:2]
    connections = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
        (5, 9), (9, 13), (13, 17),
    ]
    pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
    for a, b in connections:
        cv2.line(frame, pts[a], pts[b], (0, 200, 255), 2)
    for x, y in pts:
        cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)


def is_metal_sign(landmarks):
    def up(tip, pip):
        return landmarks[tip].y < landmarks[pip].y

    def down(tip, pip):
        return landmarks[tip].y > landmarks[pip].y

    return up(8, 6) and down(12, 10) and down(16, 14) and up(20, 18)


def recep(landmarks):
    def down(tip, pip):
        return landmarks[tip].y > landmarks[pip].y

    return (
        down(8, 5) and
        down(12, 9) and
        down(16, 13) and
        down(20, 17) and
        down(4, 6)
    )


def is_heart_sign(landmarks_list):
    if len(landmarks_list) < 2:
        return False

    for lm in landmarks_list:
        index_up    = lm[8].y  = lm[6].y
        middle_down = lm[12].y = lm[10].y
        ring_down   = lm[16].y = lm[14].y
        pinky_down  = lm[20].y = lm[18].y
        if not (index_up and middle_down and ring_down and pinky_down):
            return False

    lm0, lm1 = landmarks_list[0], landmarks_list[1]

    dist_index = math.sqrt(
        (lm0[8].x - lm1[8].x) ** 2 +
        (lm0[8].y - lm1[8].y) ** 2
    )
    dist_thumb = math.sqrt(
        (lm0[4].x - lm1[4].x) ** 2 +
        (lm0[4].y - lm1[4].y) ** 2
    )

    return dist_index < 0.09 and dist_thumb < 0.09


base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.75,
    min_hand_presence_confidence=0.75,
    min_tracking_confidence=0.75,
)

cap = cv2.VideoCapture(0)

metal_hold_counter = 0
metal_last_trigger = 0
metal_triggered = False

heart_hold_counter = 0
heart_last_trigger = 0
heart_triggered = False

recep_hold_counter = 0
recep_last_trigger = 0
recep_triggered = False

cv2.imshow("Orges Bday Geschenk  |  ESC = Beenden", popup_image)
cv2.waitKey(0)
popup_with_text = popup_image.copy()

cv2.putText(
    popup_with_text,
    "Happy Birthday Twinchacho! , mach die gleiche Geste wie die zwei geilen Typen hier!",
    (100, 800),
    cv2.FONT_HERSHEY_SIMPLEX,
    2,
    (0, 255, 0),
    2,
)

cv2.imshow("Orges Bday Geschenk  |  ESC = Beenden", popup_with_text)
cv2.waitKey(0)

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
        heart_detected = False
        recep_detected = False
        now = time.time()

        metal_cooldown = (now - metal_last_trigger) < COOLDOWN_SECONDS
        heart_cooldown = (now - heart_last_trigger) < COOLDOWN_SECONDS
        recep_cooldown = (now - recep_last_trigger) < COOLDOWN_SECONDS

        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                draw_landmarks(frame, landmarks)
                if is_metal_sign(landmarks):
                    metal_detected = True
                if recep(landmarks):
                    recep_detected = True

            if is_heart_sign(result.hand_landmarks):
                heart_detected = True

        if metal_detected and not metal_cooldown:
            metal_hold_counter += 1
        else:
            metal_hold_counter = max(0, metal_hold_counter - 2)

        if heart_detected and not heart_cooldown:
            heart_hold_counter += 1
        else:
            heart_hold_counter = max(0, heart_hold_counter - 2)

        if recep_detected and not recep_cooldown:
            recep_hold_counter += 1
        else:
            recep_hold_counter = max(0, recep_hold_counter - 2)

        h, w = frame.shape[:2]

        progress = min(metal_hold_counter / HOLD_FRAMES_REQUIRED, 1.0)
        bar_width = int(progress * w)
        bar_color = (0, 255, 100) if not metal_cooldown else (100, 100, 100)

        # Metal progress bar (top)
        cv2.rectangle(frame, (0, 30), (w, 55), (40, 40, 40), -1)
        if bar_width > 0:
            cv2.rectangle(frame, (0, 30), (bar_width, 55), bar_color, -1)
        cv2.rectangle(frame, (0, 30), (w, 55), (200, 200, 200), 1)

        # Heart progress bar (below metal bar)
        heart_progress = min(heart_hold_counter / HOLD_FRAMES_REQUIRED, 1.0)
        heart_bar_width = int(heart_progress * w)
        heart_bar_color = (180, 60, 255) if not heart_cooldown else (100, 100, 100)
        cv2.rectangle(frame, (0, 60), (w, 85), (40, 40, 40), -1)
        if heart_bar_width > 0:
            cv2.rectangle(frame, (0, 60), (heart_bar_width, 85), heart_bar_color, -1)
        cv2.rectangle(frame, (0, 60), (w, 85), (200, 200, 200), 1)

        if metal_hold_counter >= HOLD_FRAMES_REQUIRED and not metal_cooldown:
            web.open(URL)
            metal_last_trigger = now
            metal_hold_counter = 0
            metal_triggered = True

        if heart_hold_counter >= HOLD_FRAMES_REQUIRED and not heart_cooldown:
            random_path = random.choice(IMAGE_PATHS)
            popup_image2 = cv2.imread(random_path)
            cv2.imshow("Love u Twin!", popup_image2)
            cv2.waitKey(2000)
            cv2.destroyWindow("Love u Twin!")
            heart_last_trigger = now
            heart_hold_counter = 0
            heart_triggered = True

        if recep_hold_counter >= HOLD_FRAMES_REQUIRED and not recep_cooldown:
            popup_image2 = cv2.imread(RecepBild)
            cv2.imshow("hahahaha", popup_image2)
            cv2.waitKey(2000)
            cv2.destroyWindow("hahahaha")
            recep_last_trigger = now
            recep_hold_counter = 0
            recep_triggered = True

        if metal_cooldown:
            remaining = COOLDOWN_SECONDS - (now - metal_last_trigger)
            label = f"Cooldown... {remaining:.1f}s"
            color = (100, 200, 255)
        elif metal_detected:
            label = f"Halte die Geste! ({metal_hold_counter}/{HOLD_FRAMES_REQUIRED})"
            color = (0, 255, 100)
        else:
            label = "Mach die gleiche Geste wie im Bild"
            color = (0, 0, 200)

        cv2.putText(frame, label, (10, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 3)

        if heart_cooldown:
            remaining_h = COOLDOWN_SECONDS - (now - heart_last_trigger)
            heart_label = f"Herz Cooldown... {remaining_h:.1f}s"
            heart_color = (100, 200, 255)
        elif heart_detected:
            heart_label = f"Herz erkannt! Halte! ({heart_hold_counter}/{HOLD_FRAMES_REQUIRED})"
            heart_color = (180, 60, 255)
        else:
            heart_label = "Oder: Forme ein Herz mit beiden Haenden!"
            heart_color = (180, 60, 255)

        cv2.putText(frame, heart_label, (10, 290), cv2.FONT_HERSHEY_SIMPLEX, 1, heart_color, 3)

        if metal_triggered and metal_cooldown:
            cv2.putText(frame, "Das ist nicht alles!", (30, 200),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 100), 3)

        if heart_triggered and heart_cooldown:
            cv2.putText(frame, "Awww, wie suess! <3", (30, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (180, 60, 255), 3)

        cv2.imshow("Orges Bday Geschenk  |  ESC = Beenden", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

cap.release()
cv2.destroyAllWindows()
