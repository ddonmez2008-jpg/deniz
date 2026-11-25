# Video style C: reverse-engineered motion rules (from the Skedul AI SaaS explainer)

Reference: "SaaS Explainer Video for AI Startup Skedul" (31.9 s, 1080p30, 954 frames), supplied by the teacher on 2026-11-21 as a visual reference only. None of its content is reused. Only the motion system is copied, re-skinned in palette 5 (Sand + Deep Teal), and kept flat (the teacher rejected 3D tilt).
Demos:
- `render/demo_ref.py` → STYLE_C_Demo_Skedul_Style_15s.mp4 (s02, reference pacing). The teacher found it too fast.
- `render/demo_ref2.py` → STYLE_C2_Calm_Educational_Demo_15s.mp4 (s06, **C-calm** pacing). Approved.
- `render/demo_ref3.py` → STYLE_C3_Calm_Headings_SourcePage_Demo_26s.mp4 (s06, adds the heading HUD and the source-page scroll). Approved; full rebuild ordered.
- Full rebuild engine:
  - `render/calm.py`: shot library and HUD.
  - `render/typo.py`: type system.
  - `render/scenes_calm.py`: the 13 scene specs.
  - `render/audit_calm.py`: frame audit.
  - `render/finalize_calm.py`: joins the scenes and adds the audio.

## Measured facts (reference)
- **Shot length:** 10 cuts in 31.9 s. Shots last 1.4–5.4 s, about 2.6 s on average.
- **Speed ramp on every move:**
  - Fast expo-out entrance, about 6 frames to 97%.
  - A slow drift of about 1% over 0.5 s.
  - An expo-in exit over about 5 frames.
  - A hard cut at peak exit speed.
- **Hero word:** its height drifts −4% over 1 s while the letters appear blurred. It is deleted right to left at 1 letter per 2 frames.
- **Data bars** slide in horizontally with streak blur and a 2-frame stagger. Placeholders turn into labelled content about 0.15 s later.

## The nine rules
1. **R1 Speed ramp:** fast in, slow drift, fast out.
2. **R2 Cuts at peak exit speed,** hidden by blur and scale.
3. **R3 Blur drives every transition:** blur to sharp on the way in, sharp to blur on the way out. UI exits use a rack-focus blur-out.
4. **R4 Text is typed or decoded letter by letter.** A new word arrives in accent and settles to ink.
5. **R5 Ambient blobs:** huge soft TINT and teal blobs orbit slowly near the frame edges.
6. **R6 Construction guides:** a dashed box with corner handles shrinks onto the key term, with full-width dashed guide lines and a slow zoom-out while it types.
7. **R7 One full-screen accent "slam" per section:** the text decodes, then the frame morphs into a card, then the card shrinks away.
8. **R8 UI motion:** cards rise, bars streak in staggered, and placeholders turn into content.
9. **R9 Cursor and outline draw-on:** a cursor clicks on the spoken word, and a card's outline traces itself before its fill appears.

## C-calm: educational pacing (approved direction, 2026-11-21)

| Setting | Reference | C-calm |
|---|---|---|
| Entrance | 0.2 s expo-out | 0.45–0.6 s cubic-out |
| Exit | 0.17 s expo-in | 0.35 s cubic-in |
| Shot length | about 2.6 s | 4–8 s, cut on sentence boundaries |
| Max blur | 24 px | 12–14 px |
| Typing speed | 34–40 cps | 22–24 cps |
| Decode | 0.32 s | 0.6 s |
| Bar stagger | 2 frames | 4 frames, 0.8 s bars |
| Blob speed | 100% | 55% |

- **One focal action at a time,** with at least about 1.5 s of readable hold after each build.
- **Shared-element morphs instead of cuts where possible.**
- **Consecutive card shots keep the card frame;** only the content swaps inside it.
- **Real footage** sits inside a rounded photo tile beside the text, never full screen.
- **Card labels and bar tracks appear before their bars fill.**

## Teacher additions (2026-11-21)
- **Heading HUD:**
  - **Top-right:** the MAIN section heading (Introduction / Analysis / Development / Conclusion), with a 4-step tracker underneath. It decodes only when the section changes (s01 Introduction; s02–s08 Analysis; s09–s11 Development; s12 Conclusion).
  - **Top-left:** the scene's theme, retyped at each scene start.
- **Source page on first mention:** the first time any source is named (Source A/B/C or a named study), show the real article page in a browser-frame card, with a chip naming the source and a smooth ~2.3 s scroll. Then a floating stat card with the key number, and the citation under the frame.
  - Pages are captured from the live sites with Claude in Chrome: two viewport shots, stitched (`tools_local/stitch.py`), sticky and floating widgets masked, and the article column cropped so the text is readable.
  - Stored in `assets/sources/`. If a page can't be captured, show a plain citation card, never an imitation of the publisher's page.
  - ScienceDirect may show a robot check that the teacher must pass in Chrome. Other sites need extension site permission.
- **Length:** 9:30–10:00. The rebuild reuses the approved audio: scene length = 0.35 s lead + voice + 0.8 s tail, 9:49.6 in total. Don't rush the animation to save time.

## Polish pass: "premium, not AI-made" (approved before/after, 2026-11-21)
- **Type:**
  - **Literata** (a reading face for long-form digital books, which fits the subject) for every headline, statement, number and node title.
  - **Source Sans 3** for labels, captions, axes, citations and subtitles.
  - Both are SIL OFL, converted to TTF in `/home/claude/fonts`.
  - Don't use Inter.
  - Check glyph coverage: the latin subsets have no → or ≈. Write "up from 77.13" instead of an arrow.
- **Remove template chrome:**
  - No tracked ALL-CAPS eyebrow labels above headings.
  - No "·" meta strings; use commas.
  - No chip-style pills; a callout is a short coloured rule beside a plain sentence.
  - Sentence case everywhere, including source chips ("Source A", "Wang et al. (2026)").
- **One sheet per data shot:**
  - Hairline rule border, soft long shadow, radius 22.
  - Inner structure comes from thin rules and whitespace, never boxes inside boxes.
  - What the evidence is ("Field experiment, change vs control group") goes in one quiet footer line with the citation (`meta()`). The footer drops a kicker that only repeats the source name.
- **Colour has a job:**
  - Teal and brick mark data, ticks and crosses only. They never colour a headline line or a single phrase.
  - Typed letters may arrive in teal and settle to ink (motion, not a static accent).
  - Background blobs at about 60% strength.
- **HUD:** the section name in Literata, top-right, with the tracker; the theme in sentence case, top-left. No pill.
- **Captions:** a photo shot's label sits under the statement after a short teal rule. Captions that repeat the HUD (e.g. "Closing insight", "Development 2") are cut.
- **Empty sheets:** if a split column won't be spoken for more than 2.5 s, show its heading quietly in grey so the sheet is never blank.
- **QA every frame before rendering:**
  - `audit_calm.py` checks text/text overlaps, text past the safe area or the subtitle band, text overflowing the card, and text overflowing the stat card.
  - Then a contact sheet with 2 frames per shot for all 13 scenes, reviewed by eye.

## House constraints kept
- Palette 5.
- Plain subtitles with no box.
- Source A/B/C attribution.
- Illustrative interfaces labelled as such.
- No music.
- Graphics stay above y ≈ 900.
