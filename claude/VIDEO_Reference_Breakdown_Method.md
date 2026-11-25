# Breaking down the user's example video

The user supplies an example motion-graphics video (MP4) whose style they like. Measure it, look at it frame by frame, explain *why* each move works, and translate it into this skill's system. Copy only the **motion and design grammar**, never the content, text, logos, brand or characters.

## 1. Measure
```
python3 scripts/analyze_reference.py example.mp4 ref_analysis
```
This produces:
- `report.md`: shot count and lengths, cuts per minute, hard vs soft transitions, motion bursts with easing family, palette, saturation and luma, and speech pace.
- `keyframes/`: first, middle and last frame of each shot.
- `sheets/`: one frame every 0.25 s.
- `ocr.json`: on-screen text.
- `words.json`: narration timing.

The measurements are a starting point. Cuts hidden by blur or zoom can be missed, so **confirm every cut on the sheets**.

## 2. Look, every frame
Open every sheet and every keyframe. For fast moves, pull exact frames:
```
ffmpeg -ss <t> -i example.mp4 -frames:v 10 -vf "select=1,scale=640:-2,tile=5x2" f.png
```
That gives 10 consecutive frames on one image. Count frames to settle (e.g. "97% in 6 frames").

## 3. Write the breakdown (send it in the chat, and save it as `STYLE_<name>_breakdown.md` next to the project)
Cover every heading below. For each item give **the measured fact → why the designer did it (its function) → how it relates to the other elements → how we reproduce it in our engine**.

1. **Format and rhythm:** duration, fps, aspect, shot count, median and min/max shot length, cuts per minute. Do cuts land on words or sentence ends (`cuts_within_…` in report.md)? What sets the rhythm: music beats, narration, or a fixed grid?
2. **Transition grammar:** hard cut, whip, zoom-through, blur-through, dissolve, shared-element morph or mask wipe. Where does each one appear, and why (a section change vs a continuation of the same idea)?
3. **Motion curves:** easing family per move type (entrance, exit, camera, data). Durations in frames, overshoot or none, settle time, stagger between elements, any speed ramps (fast in, slow drift, fast out). Explain the effect: for example, an expo-out entrance reads as confident and an ease-in exit hides the cut.
4. **Typography:** families (serif or sans, geometric or grotesk), weights, size ratio between levels (hero : headline : body : label), tracking, case, line length, alignment and grid margins. How text enters: per word, per letter, mask rise, decode or typing, and at what speed. Hierarchy: what the eye reads first, and why.
5. **Language system:** how many words are on screen at once, headline style (noun phrase vs sentence), where numbers carry the message, and whether on-screen text repeats the narration or complements it. How labels, kickers and citations are phrased.
6. **Colour:** background and surface colours, the one accent and its job (what it marks), the contrast colour, footage grading (saturation, warmth), and dark vs light scenes. Give the palette as hex from palette.json, cleaned up by eye.
7. **Layout:** safe margins, column grid, where the eye lands in each shot, use of empty space, and how footage and graphics share the frame (full-bleed, inset tile, split).
8. **Footage use:** share of footage vs graphics, shot types (wide, detail, hands, faces), camera motion inside clips, and how text sits on footage (scrim, blur, colour block).
9. **Data and diagram style:** bars, rings, counters and nodes. How they build (tracks first, then fills), number counting, labels, and units.
10. **Texture and finish:** grain, vignette, blur, shadows, 3D or flat, sound design if any.
11. **Correlations:** the 5–10 rules that tie everything together (for example: "every entrance is the mirror of the previous exit", "accent colour appears only on the spoken keyword", "one focal action at a time with a 1.5 s readable hold").
12. **Translation table:** for each finding, the matching engine setting or new component, plus what we deliberately change for an *educational* IA video. Typical changes:
    - slower entrances (0.45–0.6 s instead of 0.2 s);
    - shots of 4–8 s cut on sentence ends;
    - a readable hold of at least 1.5 s after each build;
    - no music;
    - subtitles kept clear (graphics above y ≈ 900);
    - citations on every evidence shot;
    - Source A/B/C pages shown on first mention;
    - always hybrid footage + graphics.

## 4. Turn it into settings
- Update the motion constants (spring durations and damping, stagger, transition type and length) and the typography sizes in the build.
- Offer the example's palette as palette **0** alongside the five house palettes (see SKILL.md step 3).
- Render a **10-second style demo** (an evidence scene with footage, a graphic, subtitles, the corner heading and a source page) and get the user's approval before the full build.

## Worked example (a SaaS explainer reference, 31.9 s)
- **Measured:** 10 cuts, shots of 1.4–5.4 s (2.6 s average). Each move has a fast expo-out entrance (about 6 frames to 97%), then about 1% drift over 0.5 s, then an expo-in exit (about 5 frames), with the hard cut at peak exit speed. A hero word drifts −4% in size while its letters arrive blurred and are deleted right to left at 1 letter per 2 frames. Data bars streak in with a 2-frame stagger, and placeholders become labelled content about 0.15 s later.
- **Rules derived:** speed ramp on every move; cuts at peak exit speed hidden by blur; blur drives every transition; letter-by-letter typing or decoding; slow ambient colour blobs near the edges; construction guides around the key term; one full-screen accent "slam" per section; cards rise and bars streak; cursor and outline draw-on.
- **Educational "calm" translation that was approved:**

  | Setting | Reference | Calm version |
  |---|---|---|
  | Entrance | 0.2 s expo-out | 0.45–0.6 s cubic-out |
  | Exit | 0.17 s | 0.35 s cubic-in |
  | Shot length | about 2.6 s | 4–8 s |
  | Max blur | 24 px | 12–14 px |
  | Typing speed | 34–40 cps | 22 cps |
  | Bar stagger | 2 frames | 4 frames |
  | Blob speed | 100% | 55% |

  The 3D tilt was removed at the teacher's request, and real footage sits in rounded tiles inside cards for that style.
