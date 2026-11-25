"""Join rendered scenes, build the padded voice track to match exactly, mux, loudnorm."""
import subprocess, os, sys
import build  # build.py = engine_core + this video's scene builders (copy build_template.py)
from lib import FPS

ROOT = build.ROOT
OUT = os.path.join(ROOT, os.environ.get('IA_VIDEO_OUT', 'out/IA_demo_video.mp4'))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
os.makedirs(f'{ROOT}/tmp_audio', exist_ok=True)
parts = []
for sid in build.ORDER:
    S = build.make_scene(sid)
    n = int(round(S.L * FPS))
    dur = n / FPS
    wav = f'{ROOT}/tmp_audio/{sid}.wav'
    ms = int(build.LEAD * 1000)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{ROOT}/audio/{sid}.mp3', '-af',
                    f'adelay={ms}|{ms},apad,atrim=0:{dur:.6f}', '-ar', '48000', '-ac', '2', wav], check=True)
    parts.append((sid, f'{ROOT}/scenes3/{sid}.mp4', wav, dur))
    for sh in S.shots:
        sh.close()
with open(f'{ROOT}/tmp_audio/v.txt', 'w') as f:
    for _, v, _, _ in parts:
        f.write(f"file '{v}'\n")
with open(f'{ROOT}/tmp_audio/a.txt', 'w') as f:
    for _, _, a, _ in parts:
        f.write(f"file '{a}'\n")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{ROOT}/tmp_audio/a.txt',
                '-c', 'copy', f'{ROOT}/audio/voiceover.wav'], check=True)
tmp = OUT.replace('.mp4', '.tmp.mp4')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{ROOT}/tmp_audio/v.txt',
                '-i', f'{ROOT}/audio/voiceover.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                '-movflags', '+faststart', tmp], check=True)
os.replace(tmp, OUT)
print('total', sum(p[3] for p in parts), OUT)
