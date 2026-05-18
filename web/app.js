import { HandLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";

// ── Config ──
const SPOTIFY_URL   = "https://open.spotify.com/playlist/2pUqkWhPN35vwvIG2QSVnl";
const HOLD_REQUIRED = 20;
const COOLDOWN_S    = 5;
const RANDOM_IMAGES = ["../meinBromeinTwin.jpg", "../Stalin.PNG", "../Leckermaul.jpeg", "../pic.JPG", "../up.jpg"];
const RECEP_IMAGE   = "../goat.jpg";

// ── DOM ──
const introEl    = document.getElementById("intro");
const loadingEl  = document.getElementById("loading");
const errorEl    = document.getElementById("error");
const errorMsg   = document.getElementById("errorMsg");
const appEl      = document.getElementById("app");
const video      = document.getElementById("video");
const canvas     = document.getElementById("canvas");
const ctx        = canvas.getContext("2d");
const popup          = document.getElementById("popup");
const popupImg       = document.getElementById("popupImg");
const popupText      = document.getElementById("popupText");
const spotifyOverlay = document.getElementById("spotifyOverlay");
const spotifyBtn     = document.getElementById("spotifyBtn");

spotifyBtn.addEventListener("click", () => {
  spotifyOverlay.classList.remove("visible");
});
const metalBar   = document.getElementById("metalBar");
const heartBar   = document.getElementById("heartBar");
const metalLabel = document.getElementById("metalLabel");
const heartLabel = document.getElementById("heartLabel");

// ── State ──
let metalCounter = 0, metalLastTrigger = 0, metalTriggered = false;
let heartCounter = 0, heartLastTrigger = 0, heartTriggered = false;
let recepCounter = 0, recepLastTrigger = 0;
let handLandmarker = null;
let popupTimer = null;

// ── Hand skeleton connections ──
const CONNECTIONS = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[5,6],[6,7],[7,8],
  [0,9],[9,10],[10,11],[11,12],
  [0,13],[13,14],[14,15],[15,16],
  [0,17],[17,18],[18,19],[19,20],
  [5,9],[9,13],[13,17],
];

// ── Gesture detection (ported from Python) ──
function isMetalSign(lm) {
  const up   = (t, p) => lm[t].y < lm[p].y;
  const down = (t, p) => lm[t].y > lm[p].y;
  return up(8, 6) && down(12, 10) && down(16, 14) && up(20, 18);
}

function isRecep(lm) {
  const down = (t, p) => lm[t].y > lm[p].y;
  return down(8, 5) && down(12, 9) && down(16, 13) && down(20, 17) && down(4, 6);
}

function isHeartSign(all) {
  if (all.length < 2) return false;
  const [a, b] = all;
  return Math.hypot(a[8].x - b[8].x, a[8].y - b[8].y) < 0.15 &&
         Math.hypot(a[4].x - b[4].x, a[4].y - b[4].y) < 0.15;
}

// ── Draw hand skeleton ──
// Note: canvas has CSS scaleX(-1), so we draw at natural landmark positions
// and the CSS flip mirrors both video and landmarks correctly.
function drawLandmarks(lm, dx, dy, dw, dh) {
  const px = i => dx + lm[i].x * dw;
  const py = i => dy + lm[i].y * dh;

  ctx.strokeStyle = "rgba(0, 210, 255, 0.85)";
  ctx.lineWidth = 2;
  for (const [a, b] of CONNECTIONS) {
    ctx.beginPath();
    ctx.moveTo(px(a), py(a));
    ctx.lineTo(px(b), py(b));
    ctx.stroke();
  }
  ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
  for (let i = 0; i < 21; i++) {
    ctx.beginPath();
    ctx.arc(px(i), py(i), 4, 0, Math.PI * 2);
    ctx.fill();
  }
}

// ── Image popup ──
function showPopup(src, text = "") {
  clearTimeout(popupTimer);
  popupImg.src = src;
  popupText.textContent = text;
  popup.classList.add("visible");
  popupTimer = setTimeout(() => popup.classList.remove("visible"), 2200);
}

// ── Canvas sizing ──
function resizeCanvas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
}

// ── Main detection loop ──
function detect(ts) {
  const W = canvas.width, H = canvas.height;
  const VW = video.videoWidth, VH = video.videoHeight;

  if (!VW || !VH || video.readyState < 2) {
    requestAnimationFrame(detect);
    return;
  }

  // Cover-scale: fill canvas while preserving video aspect ratio
  const scale = Math.max(W / VW, H / VH);
  const dw = VW * scale, dh = VH * scale;
  const dx = (W - dw) / 2, dy = (H - dh) / 2;

  // Draw video frame (CSS scaleX(-1) on canvas mirrors it for the user)
  ctx.drawImage(video, dx, dy, dw, dh);

  // Run hand detection
  const result = handLandmarker.detectForVideo(video, ts);

  const now = Date.now() / 1000;
  let metalDetected = false, heartDetected = false, recepDetected = false;
  const metalCool = (now - metalLastTrigger) < COOLDOWN_S;
  const heartCool = (now - heartLastTrigger) < COOLDOWN_S;
  const recepCool = (now - recepLastTrigger) < COOLDOWN_S;

  if (result.landmarks?.length) {
    const lms = result.landmarks;
    // If any hand has the index finger up, suppress recep to avoid false triggers during heart gestures
    const anyIndexUp = lms.some(lm => lm[8].y < lm[6].y);
    for (const lm of lms) {
      drawLandmarks(lm, dx, dy, dw, dh);
      if (isMetalSign(lm)) metalDetected = true;
      if (!anyIndexUp && isRecep(lm)) recepDetected = true;
    }
    if (isHeartSign(lms)) heartDetected = true;
  }

  // Update hold counters
  metalCounter = metalDetected && !metalCool
    ? Math.min(metalCounter + 1, HOLD_REQUIRED)
    : Math.max(0, metalCounter - 2);

  heartCounter = heartDetected && !heartCool
    ? Math.min(heartCounter + 1, HOLD_REQUIRED)
    : Math.max(0, heartCounter - 2);

  recepCounter = recepDetected && !recepCool
    ? Math.min(recepCounter + 1, HOLD_REQUIRED)
    : Math.max(0, recepCounter - 2);

  // Progress bars
  metalBar.style.width = (metalCounter / HOLD_REQUIRED * 100) + "%";
  heartBar.style.width = (heartCounter / HOLD_REQUIRED * 100) + "%";

  // Trigger: Metal → Spotify overlay (window.open blocked by browser outside user gesture)
  if (metalCounter >= HOLD_REQUIRED && !metalCool) {
    spotifyBtn.href = SPOTIFY_URL;
    spotifyOverlay.classList.add("visible");
    metalLastTrigger = now;
    metalCounter = 0;
    metalTriggered = true;
  }

  // Trigger: Heart → random image
  if (heartCounter >= HOLD_REQUIRED && !heartCool) {
    showPopup(RANDOM_IMAGES[Math.floor(Math.random() * RANDOM_IMAGES.length)], "Hab dich Lieb Brotato Chip");
    heartLastTrigger = now;
    heartCounter = 0;
    heartTriggered = true;
  }

  // Trigger: Recep → goat
  if (recepCounter >= HOLD_REQUIRED && !recepCool) {
    showPopup(RECEP_IMAGE);
    recepLastTrigger = now;
    recepCounter = 0;
  }

  // Update labels
  if (metalCool) {
    metalLabel.textContent = `⏳ Cooldown... ${(COOLDOWN_S - (now - metalLastTrigger)).toFixed(1)}s`;
    metalLabel.className = "hud-label cool";
    metalBar.className   = "progress-fill fill-cool";
  } else if (metalDetected) {
    metalLabel.textContent = `🤘 Halte die Geste! (${metalCounter}/${HOLD_REQUIRED})`;
    metalLabel.className = "hud-label metal";
    metalBar.className   = "progress-fill fill-metal";
  } else {
    metalLabel.textContent = metalTriggered
      ? "🤘 Das ist nicht alles! Mach das Herz!"
      : "🤘 Mach die Metal-Geste!";
    metalLabel.className = "hud-label metal";
    metalBar.className   = "progress-fill fill-metal";
  }

  if (heartCool) {
    heartLabel.textContent = `⏳ Herz Cooldown... ${(COOLDOWN_S - (now - heartLastTrigger)).toFixed(1)}s`;
    heartLabel.className = "hud-label cool";
    heartBar.className   = "progress-fill fill-cool";
  } else if (heartDetected) {
    heartLabel.textContent = `🤍 Herz erkannt! Halte! (${heartCounter}/${HOLD_REQUIRED})`;
    heartLabel.className = "hud-label heart";
    heartBar.className   = "progress-fill fill-heart";
  } else {
    heartLabel.textContent = heartTriggered
      ? "🤍 Awww! Forme noch eines! 💜"
      : "🤍 Forme ein Herz mit beiden Händen!";
    heartLabel.className = "hud-label heart";
    heartBar.className   = "progress-fill fill-heart";
  }

  requestAnimationFrame(detect);
}

// ── Init ──
document.getElementById("startBtn").addEventListener("click", async () => {
  introEl.classList.add("fade-out");
  setTimeout(() => { introEl.style.display = "none"; }, 500);
  loadingEl.classList.add("visible");

  try {
    // Load MediaPipe (WASM + model from CDN — no local files needed)
    const filesetResolver = await FilesetResolver.forVisionTasks(
      "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );
    handLandmarker = await HandLandmarker.createFromOptions(filesetResolver, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        delegate: "GPU",
      },
      runningMode: "VIDEO",
      numHands: 2,
      minHandDetectionConfidence: 0.75,
      minHandPresenceConfidence: 0.75,
      minTrackingConfidence: 0.75,
    });

    // Start camera
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    });
    video.srcObject = stream;
    await new Promise((res, rej) => { video.onloadedmetadata = res; video.onerror = rej; });
    await video.play();

    // Show app
    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);
    loadingEl.classList.remove("visible");
    appEl.classList.add("visible");

    requestAnimationFrame(detect);

  } catch (e) {
    loadingEl.classList.remove("visible");
    errorMsg.textContent = e.name === "NotAllowedError"
      ? "Kamera-Zugriff verweigert. Bitte erlaube die Kamera und lade die Seite neu."
      : "Fehler: " + (e.message || e);
    errorEl.classList.add("visible");
  }
});
