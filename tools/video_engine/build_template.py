"""Per-video scene builders. Copy to build.py, then fill ORDER, the section map and one build_<sid>(S) per scene.

qa.py and finalize.py import this module as `build`. Everything generic (Scene, Shot, foot(), chapter(),
statement(), gfx(), render(), ...) comes from engine_core; ORDER and BUILDERS are the shared engine_core objects.

Usage:
    python3 build.py stills s01          # stills at the busiest moment of every shot -> stills/
    python3 build.py render s01 s02 ...  # encode scenes -> scenes3/<sid>.mp4
"""
import sys
import engine_core
from engine_core import *  # noqa: F401,F403
import overlays

# 1. Play order (shared list object: mutate it, don't rebind it).
engine_core.ORDER[:] = ['s01', 's02', 's03', 's04', 's05', 's06', 's07', 's07b', 's08', 's09', 's10', 's11', 's12']
ORDER = engine_core.ORDER

# 2. Main section label (top-right): 0 Introduction, 1 Analysis, 2 Development, 3 Conclusion.
#    The answer scene goes under Conclusion. FIRST_OF = first scene of each heading (label springs in).
overlays.SCENE_SECTION.clear()
overlays.SCENE_SECTION.update({'s01': 0, 's02': 0, 's03': 1, 's04': 1, 's05': 1, 's06': 1, 's07': 1, 's07b': 1,
                               's08': 3, 's09': 2, 's10': 2, 's11': 2, 's12': 3})
overlays.FIRST_OF.clear()
overlays.FIRST_OF.update({'s01', 's03', 's08', 's09', 's12'})


# 3. One builder per scene. Key EVERY animation to a spoken phrase with S.T("exact phrase").
#    Alternate foot() footage shots with paper motion-graphics shots; cut every 4-8 s on sentence ends.
def build_s01(S):
    raise NotImplementedError('write build_s01: e.g. S.add(0.0, foot(...), clip="office", push=(1.0, 1.06))')


# ... build_s02 ... build_s12

BUILDERS.update({sid: globals()[f'build_{sid}'] for sid in ORDER if f'build_{sid}' in globals()})

if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'stills':
        sid = sys.argv[2]
        S = make_scene(sid)
        ts = [(S.shots[i].t0 + S.shots[i].t1) / 2 + 0.25 * (S.shots[i].t1 - S.shots[i].t0) for i in range(len(S.shots))]
        render(sid, stills=ts)
        print(sid, [round(s.t0, 1) for s in S.shots], round(S.L, 1))
    elif mode == 'render':
        for sid in sys.argv[2:]:
            render(sid)
