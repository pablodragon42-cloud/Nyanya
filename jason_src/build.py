# Build the whole short:  python build.py [video] [audio] [mux]   (no args = all three)
# Needs: ffmpeg, python packages numpy, scipy, pillow (faster-whisper only to redo words_asr.json).
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.environ.get("BUILD", os.path.join(HERE, "build"))
OUT = os.environ.get("OUT", os.path.join(os.path.dirname(HERE), "jason_drug_idiot_9x16.mp4"))
PY = sys.executable
JOBS = int(os.environ.get("JOBS", "4"))


def video():
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    n = int(round(tl["duration"] * tl["fps"]))
    edges = [round(i * n / JOBS) for i in range(JOBS + 1)]
    procs = []
    t0 = time.time()
    for i in range(JOBS):
        part = os.path.join(BUILD, f"part_{i}.mp4")
        procs.append(subprocess.Popen([PY, os.path.join(HERE, "render.py"), "range", str(edges[i]), str(edges[i + 1]), part],
                                      cwd=HERE, env=dict(os.environ, BUILD=BUILD)))
    for p in procs:
        if p.wait() != 0:
            sys.exit("render failed")
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for i in range(JOBS):
            f.write(f"file 'part_{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(BUILD, "video.mp4")], check=True)
    print(f"video: {n} frames in {time.time() - t0:.0f}s")


def audio():
    subprocess.run([PY, os.path.join(HERE, "sound.py")], cwd=HERE, check=True, env=dict(os.environ, BUILD=BUILD))


def mux(vbit="9M"):
    """final delivery encode: 2-pass H.264 at a fixed bitrate (film grain on every frame makes CRF files huge),
    AAC stereo audio. Keeps the file well under 100 MB."""
    src = os.path.join(BUILD, "video.mp4")
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", vbit, "-maxrate", "12M", "-bufsize", "18M",
              "-pix_fmt", "yuv420p", "-profile:v", "high", "-r", "30"]
    plog = os.path.join(BUILD, "x264pass")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src] + common +
                   ["-pass", "1", "-passlogfile", plog, "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", os.path.join(BUILD, "mix.wav"),
                    "-map", "0:v", "-map", "1:a"] + common + ["-pass", "2", "-passlogfile", plog,
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("wrote", OUT, f"{os.path.getsize(OUT) / 1e6:.1f} MB")


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    steps = sys.argv[1:] or ["video", "audio", "mux"]
    for s in steps:
        {"video": video, "audio": audio, "mux": mux}[s]()
