# Build data.js for the canvas renderer from ../jason_src/timeline.json
# speakers: n = narrator (scared friend telling the story), s = scared friend's quote, i = idiot's quote
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(HERE, "..", "jason_src", "timeline.json"), encoding="utf-8"))
fps = tl["fps"]
nf = int(round(tl["duration"] * fps))
env = tl["env"] + [0.0] * max(0, nf - len(tl["env"]))

def speaker(t):
    for q in tl["quotes"]:
        if q["s"] - 0.05 <= t <= q["e"] + 0.05:
            return "i" if q["who"] == 2 else "s"
    return "n"

words = [dict(s=w["s"], e=w["e"], w=w["w"], sc=w["scene"], i=w["i"], sp=speaker((w["s"] + w["e"]) / 2))
         for w in tl["words"]]
mouth = {k: [0.0] * nf for k in "nsi"}
for f in range(nf):
    sp = speaker(f / fps)
    mouth[sp][f] = round(env[f], 3)
data = dict(fps=fps, dur=tl["duration"], nf=nf, words=words, mouth=mouth,
            quotes=[dict(q, sp="i" if q["who"] == 2 else "s") for q in tl["quotes"]])
open(os.path.join(HERE, "data.js"), "w", encoding="utf-8").write("const DATA = " + json.dumps(data, ensure_ascii=False) + ";\n")
print("frames", nf, "words", len(words))
