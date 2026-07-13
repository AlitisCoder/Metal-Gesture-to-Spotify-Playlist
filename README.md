<div align="center">

# 🤘 Metal Gesture → Spotify

**Throw the horns at your webcam, and your rock playlist opens itself.**
A tiny computer-vision app that recognises the metal sign 🤘 in real time and launches a Spotify playlist — no clicks, no API keys, no login.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-realtime-5C3EE8?logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Hand%20Landmarker-00A67E?logo=google&logoColor=white)
![License MIT](https://img.shields.io/badge/License-MIT-F2B33D)

<!-- Demo-GIF hier einbinden — bei einer Webcam-App das Wichtigste überhaupt: -->
<!-- ![Demo](docs/demo.gif) -->

</div>

---

## Die Geschichte

Das hier ist für einen Freund entstanden. Wir hören beide Rock, haben zusammen eine
Playlist aufgebaut — die ist im Grunde das Fundament unserer Freundschaft. Also
brauchte sie einen Auslöser, der zu uns passt: kein Button, sondern das Metal-Zeichen.
Hand heben, Hörner zeigen, Musik läuft.

## Was es macht

Die App öffnet die Webcam und sucht in Echtzeit nach einer Hand. Zeigt man das
**Metal-Zeichen** (🤘 — Zeige- und kleiner Finger gestreckt, Mittel- und Ringfinger
eingeklappt) und **hält es kurz**, öffnet sich die hinterlegte Spotify-Playlist im
Browser. Ein Fortschrittsbalken zeigt, wie lange man die Geste noch halten muss, und
ein kurzer Cooldown verhindert, dass sie mehrfach hintereinander auslöst.

Bewusst schlicht: Es gibt **keine Spotify-Anmeldung und keine API-Keys**. Die App
öffnet einfach die öffentliche Playlist-URL — dadurch läuft sie sofort, ohne Setup-Hürden.

## Wie es funktioniert

Der Kern ist reine Handgeometrie auf Basis der MediaPipe-Landmarks:

```
        8   12  16          Fingerspitzen (tips)
        |   |   |   20
        6   10  14  |       Mittelgelenke (pip)
         \  |   |  18
          \ |  /  /
           Handfläche
```

1. **Hand-Erkennung.** MediaPipes *Hand Landmarker* (Tasks-API, Video-Modus) liefert pro
   Frame 21 Handpunkte mit x/y-Koordinaten.
2. **Gestenlogik.** Ein Finger gilt als *gestreckt*, wenn seine Spitze höher liegt als
   sein Mittelgelenk. Das Metal-Zeichen ist damit eine klare Bedingung:

   | Finger | Spitze vs. Gelenk | Zustand |
   |---|---|---|
   | Zeigefinger | 8 über 6 | gestreckt ✅ |
   | Mittelfinger | 12 unter 10 | eingeklappt ✅ |
   | Ringfinger | 16 unter 14 | eingeklappt ✅ |
   | Kleiner Finger | 20 über 18 | gestreckt ✅ |

3. **Halten statt Zucken.** Damit ein zufälliges Handzeichen nicht sofort auslöst, muss
   die Geste ~20 Frames gehalten werden (Fortschrittsbalken). Wird sie unterbrochen,
   fällt der Zähler wieder ab — eine simple, robuste Entprellung.
4. **Auslösen & Cooldown.** Ist der Zähler voll, öffnet sich die Playlist; danach greift
   ein 5-Sekunden-Cooldown, bevor die Geste erneut wirken kann.

Zusätzlich zeichnet die App das Hand-Skelett, den Fortschrittsbalken und Status-Texte
direkt ins Kamerabild.

## Loslegen

**Voraussetzungen:** Python 3.10+ und eine Webcam.

```bash
pip install opencv-python mediapipe
python "Gesture to Spotify.py"
```

Das MediaPipe-Handmodell (`hand_landmarker.task`, ~8 MB) wird beim ersten Start
**automatisch heruntergeladen**, falls es fehlt — kein manueller Schritt nötig.
Beenden mit **ESC**.

## Anpassen

Oben im Skript lässt sich alles Wesentliche einstellen:

```python
SPOTIFY_URL           = "https://open.spotify.com/playlist/..."  # deine Playlist
HOLD_FRAMES_REQUIRED  = 20   # wie lange die Geste gehalten werden muss
COOLDOWN_SECONDS      = 5    # Pause nach dem Auslösen
```

Wer eine andere Geste möchte, passt die Bedingung in `is_metal_sign()` an — dieselbe
„Spitze über/unter Gelenk"-Logik lässt sich auf beliebige Fingerkombinationen übertragen.

## Roadmap

- **Web-Port.** Das ursprüngliche Ziel: dieselbe Idee im Browser, mit MediaPipe.js —
  dann läuft es ohne Python-Installation direkt auf einer Website.
- **Mehr Gesten → mehr Aktionen.** Verschiedene Handzeichen für Play/Pause, Skip oder
  unterschiedliche Playlists.
- **Echte Spotify-Steuerung.** Statt die Playlist nur zu öffnen, per Spotify-API direkt
  die Wiedergabe steuern.

## Tech-Stack

Python · OpenCV (Kamera & Overlay) · MediaPipe Hand Landmarker (Handtracking)

## Lizenz

MIT

---

<div align="center">
<sub>🤘 Built for a friend, powered by a shared rock playlist.</sub>
</div>
