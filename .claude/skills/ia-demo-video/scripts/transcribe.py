import json, re, time, difflib, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel('small.en', device='cpu', compute_type='int8')
S = {x['id']: x['text'] for x in json.load(open('script/scenes.json'))}
num = {'15':'fifteen','30':'thirty','40':'forty','18':'eighteen','12':'twelve','25':'twenty five','19':'nineteen','2.8':'two point eight','83':'eighty three','9':'nine','6':'six','14':'fourteen','31':'thirty one','8':'eight','175':'one hundred and seventy five','20':'twenty','17':'seventeen','55':'fifty five','5000':'five thousand','25000':'twenty five thousand'}
def norm(s):
    s=s.lower().replace('-',' ').replace('%',' percent')
    toks=re.findall(r"[a-z0-9.']+", s)
    out=[]
    for t in toks:
        t=t.strip('.')
        out += num.get(t,t).split()
    return out
def load(p):
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-f','s16le','-ac','1','-ar','16000','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.int16).astype(np.float32)/32768
for sid in sys.argv[1:]:
    segs,_ = m.transcribe(load(f'audio/{sid}.mp3'), word_timestamps=True, beam_size=5, language='en', condition_on_previous_text=False)
    words=[{'w':w.word.strip(),'s':round(w.start,3),'e':round(w.end,3)} for sg in segs for w in sg.words]
    json.dump(words, open(f'words/{sid}.json','w'))
    a,b=norm(S[sid]),norm(' '.join(x['w'] for x in words))
    sm=difflib.SequenceMatcher(None,a,b)
    diffs=[(' '.join(a[i1:i2]),' '.join(b[j1:j2])) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!='equal']
    print(sid, f'{sm.ratio():.3f}', diffs[:10], flush=True)
