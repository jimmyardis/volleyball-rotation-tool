// Film Room client-side video processing. Privacy-first: the raw clip never
// leaves the phone — we sample JPEG frames on a canvas and (for serves) run
// MediaPipe's pose landmarker locally, then upload only frames + landmarks.

const MP_VERSION = "0.10.14";
const MP_BUNDLE = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MP_VERSION}/vision_bundle.mjs`;
const MP_WASM = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MP_VERSION}/wasm`;
const MP_MODEL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task";

const MAX_CLIP_SECONDS = 20;    // frames sampled across at most this much clip
const FRAME_COUNT = 10;
const FRAME_MAX_SIDE = 512;
const POSE_FPS = 10;
const POSE_MAX_FRAMES = 80;

function loadVideo(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "auto";
    video.onloadedmetadata = () => resolve({ video, url });
    video.onerror = () => { URL.revokeObjectURL(url); reject(new Error("couldn't read that video file")); };
    video.src = url;
  });
}

function seekTo(video, t) {
  return new Promise((resolve, reject) => {
    const onSeek = () => { cleanup(); resolve(); };
    const onErr = () => { cleanup(); reject(new Error("seek failed")); };
    const cleanup = () => { video.removeEventListener("seeked", onSeek); video.removeEventListener("error", onErr); };
    video.addEventListener("seeked", onSeek);
    video.addEventListener("error", onErr);
    video.currentTime = t;
  });
}

// Sample FRAME_COUNT JPEG frames evenly across the clip.
// -> { frames: [base64...], timestamps: [s...], duration_s }
export async function extractFrames(file, onProgress) {
  const { video, url } = await loadVideo(file);
  try {
    const duration = Math.min(video.duration || 0, MAX_CLIP_SECONDS);
    if (!duration || !isFinite(duration)) throw new Error("that clip has no readable length");
    const scale = Math.min(1, FRAME_MAX_SIDE / Math.max(video.videoWidth, video.videoHeight));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);
    const ctx = canvas.getContext("2d");

    const frames = [], timestamps = [];
    for (let i = 0; i < FRAME_COUNT; i++) {
      const t = (duration * (i + 0.5)) / FRAME_COUNT;
      await seekTo(video, t);
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      frames.push(canvas.toDataURL("image/jpeg", 0.72).split(",")[1]);
      timestamps.push(Math.round(t * 10) / 10);
      onProgress?.(`Reading your clip… frame ${i + 1}/${FRAME_COUNT}`);
    }
    return { frames, timestamps, duration_s: Math.round(duration * 10) / 10 };
  } finally {
    URL.revokeObjectURL(url);
  }
}

// Run MediaPipe pose landmarking over the clip (serve metrics). Loads the
// model from a CDN; throws if that fails — callers treat pose as optional.
export async function extractPose(file, onProgress) {
  onProgress?.("Loading the motion tracker…");
  const vision = await import(/* @vite-ignore */ MP_BUNDLE);
  const fileset = await vision.FilesetResolver.forVisionTasks(MP_WASM);
  const landmarker = await vision.PoseLandmarker.createFromOptions(fileset, {
    baseOptions: { modelAssetPath: MP_MODEL },
    runningMode: "VIDEO",
    numPoses: 1,
  });

  const { video, url } = await loadVideo(file);
  try {
    const duration = Math.min(video.duration || 0, MAX_CLIP_SECONDS);
    const count = Math.min(POSE_MAX_FRAMES, Math.max(10, Math.ceil(duration * POSE_FPS)));
    const poseFrames = [];
    for (let i = 0; i < count; i++) {
      const t = (duration * i) / count;
      await seekTo(video, t);
      const res = landmarker.detectForVideo(video, Math.round(t * 1000));
      const lm = res.landmarks?.[0];
      if (lm && lm.length >= 33) {
        poseFrames.push({
          t: Math.round(t * 100) / 100,
          lm: lm.map((p) => [p.x, p.y, p.z ?? 0, p.visibility ?? 0.9]),
        });
      }
      if (i % 10 === 0) onProgress?.(`Tracking your motion… ${Math.round((i / count) * 100)}%`);
    }
    return poseFrames;
  } finally {
    URL.revokeObjectURL(url);
    landmarker.close?.();
  }
}
