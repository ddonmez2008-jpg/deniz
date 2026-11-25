# How the IA demo video was made (pipeline + rules)

Reference build: *To what extent do generative AI assistants that automate repetitive office tasks affect productivity and employment in small businesses?*. It's a 9:38 MP4 with 13 scenes, a cloned voice, real stock footage, motion graphics and word-timed subtitles. The engine code is in `tools/video_engine/`. The `/ia-demo-video` skill runs this whole pipeline.
Second build (2026-11-20): *chatbots and engagement in online English literature classes*, 9:49, voice "Alina Turenkova", palette 5. Script: `claude/IA_Demo_Video_Script_Chatbots_Online_Literature.md`.
v5 of the reference build (2026-11-21) adds the top-right main section label and real source pages on first mention (section 6b).
v6 of the reference build (2026-11-21) is the **premium remake**: IBM Plex Sans, a cooler palette, sentence-case labels, rules instead of cards, a real sources table (section 5b). This is now the default for every new video.

---

## 0. What the student/teacher gets
- One MP4 (1920×1080, 30 fps, H.264 CRF 18, AAC 192k, loudness −16 LUFS). It runs **9:30–9:55**, which keeps it under the 10-minute IA limit.
- It is delivered as a file. **No Canva export.**
- A script doc in the project (`claude/IA_Demo_Video_Script_<topic>.md`) with the Source A/B/C mapping and credits.

## 1. Script rules (non-negotiable)
1. Read `claude/00_SYSTEM_MASTER_REFERENCE.md`, `sources/IA/IA_05_Checklist_Outline_Video_C_D_E.md` and the IA guide first. The video covers criteria **C (inquiry / evidence), D (evaluation / answer) and E (emerging trends)**. It follows the IPD's inquiry question.
2. Call the three main sources **Source A, Source B and Source C** (never 1/2/3). Every claim takes the form "**According to Source X, …**". Use "**for example**" to introduce an illustration. Name other sources in full, e.g. "According to Noy and Zhang…".
3. Use teacher/student voice. Keep the writer's own connectives (So, But, Why…?, This links back…). No stock phrases. Run `tools/voice_profile.py drift <profile> <original> <new>` on every new paragraph. Remove anything it flags under `stock_phrases_introduced`. "for example" is allowed.
4. Scene plan, about 1,480 words at about 2.6 words/s:

   | Scene | Content |
   |---|---|
   | s01 | Inquiry focus |
   | s02 | How the digital system works (input → processing → output → human, plus one "for example") |
   | s03–s04 | Theme 1, with a qualification |
   | s05–s06 | Theme 2, with the owner perspective |
   | s07 | Theme 3 |
   | s07b | Weighing the evidence (strength / limit / weight per source) |
   | s08 | Answer to the inquiry question, with its limitation |
   | s09–s11 | Three emerging trends / future developments |
   | s12 | Closing insight: what would change the judgement, plus a values/equity link |

5. Write numbers as words in the script so the TTS says them correctly. Subtitles turn them back into digits automatically (`subs.py`).
6. The project instruction says: never reuse topics or content from the sample IA/EE files.

## 2. Voice (ElevenLabs)
- Use `creative_list_voices` to find the voice the user picked. The reference build used "Bugra Buyukduykular", voice_id `vFOTk95MLgA2Ak2wbxTC`.
- Make **one clip per scene** with `creative_generate_speech` (model `eleven_v4`, `generations_count: 1`). Put every clip on the same flow. Never re-call a generation to retry, because each call is charged.
- Download clips via `creative_get_generations` → `full_res_url` with `curl`, saving them to `audio/<sid>.mp3`.
- Cost is about 600–750 credits per 110-word clip.

## 3. Word timing + verification
- `python3 tools/video_engine/transcribe.py s01 s02 …` uses faster-whisper `small.en` with word timestamps. It writes `words/<sid>.json` and diffs the transcript against the script.
  - Decode audio with ffmpeg to an int16 numpy array, because the `av` decoder breaks.
  - Don't use `initial_prompt` (it makes whisper skip clip starts). Set `condition_on_previous_text=False`.
- Accept only spelling variants (summarise/summarize, licences/licenses). If a phrase is "missing", re-transcribe just that window (±2 s). If the words are there, patch the JSON. Whisper sometimes swallows 6–8 words into one long token.
- `cues.py`: `S.T("exact phrase")` gives the scene time the phrase is spoken (word time + LEAD − 0.1 s). **Every animation is keyed to a spoken phrase, never to a hard-coded second.**

## 4. Stock footage (real, not AI)
- Use Mixkit. Pexels and Pixabay return 403 from the sandbox. Search with `curl https://mixkit.co/free-stock-video/<query>/` and pull the `…-<id>/` slugs.
- `sh tools/video_engine/prep_footage.sh <id> <name>` downloads `https://assets.mixkit.co/videos/<id>/<id>-1080.mp4`. It grades the clip to 1080p30 with slightly muted colour, no audio, plus a mirrored `_flip` copy.
- About 12–14 clips per video: office, small shop, accounts, night work, typing, remote work, papers, call centre ×2, network. Remind the teacher to check the Mixkit licence.

## 5. Design system
- 1920×1080, 30 fps. Margins: 96 px left/right, 56 px top.
- Type: **IBM Plex Sans** (TTFs in the skill's `scripts/fonts/`, loaded by `lib.tf()` from `PLEX_DIR`). Section 5b has the full type scale.
- Palette (premium default, **Paper + Ink Blue v6**):

  | Role | Hex |
  |---|---|
  | BG (paper) | EDEBE6 |
  | SURF (shade) | E3E1DA |
  | TXT (ink) | 1B1F27 |
  | MUTE (graphite) | 5A606C |
  | GRID (rule) | CBC8BF |
  | ACC (ink blue) | 1F4F9E |
  | NEG (brick) | B13A2B |
  | BAR | B9B6AD |
  | LIGHT (text on footage) | F4F3EF |
  | TINT (kicker on footage) | B3CBEF |

  To change palette, edit the constants at the top of `v3style.py` and `INK`/`ACC`/`TXT`/`CUR` in `subs.py`.
- Recurring components:
  - Section label, top-left (y 60), sentence case.
  - Main section label, top-right (see 6b).
  - Kicker: 28 px Medium, sentence case, no tracking (`kicker()`; `tidy()` turns "A · B · C" into "A: B, C").
  - Mask-reveal headline (`words_reveal`: each word rises on its own spring with a 65 ms stagger).
  - `colrule()` column markers, the sources table, quiet tonal panels (`card()`, no stripe) only around charts and diagram nodes, pills, ticks and crosses.
  - Big numbers (`num_reveal`).
  - Source line, bottom-left at y 996: "Source: …" or "Sources: …; …" in 24 px graphite.
- Motion:
  - Damped springs (ζ 0.8–0.9).
  - Material "emphasized" easing for data, never overshooting on data.
  - A slow camera push on every shot.
  - A camera-driven diagram for the system explanation, with focus-dimming of non-active nodes.
  - Transitions: zoom-through with 5-sub-frame motion blur, or a crossfade.
  - Film grain at 4% (overlay blend), vignette, and a gradient scrim behind text on footage.
- Shot types:
  - `chapter()`: kicker ("Theme 1") and a huge line.
  - `foot()`: full-bleed footage with lower-left text, base y 850.
  - `statement()`: a centred two-line key phrase at 116 px (e.g. "Plausible, / not checked.").
  - Custom draw functions for data (bars, rings, the sources table, diagrams).
- Rhythm: a cut every 4–10 s. Alternate footage and paper graphics, and never run two text walls in a row.

## 5b. Premium design system (v6, default)
Approved from a before/after frame of s07b, then applied to all 13 scenes.
- **Type scale:** headlines 84 px SemiBold; statements 108–116 px; footage headlines 104–116 px; body and list text 30–54 px; labels 26–28 px Medium; citations 24 px Regular. Subtitles Plex Medium 38.
- **No template tells:** sentence case everywhere; no tracked all-caps; no "·" chains; no "01/02" numbering unless the content really is a sequence; no kicker that repeats the section label.
- **Structure follows content:**
  - s07b "Weighing the evidence" is a table: columns Source A/B/C (name + method), rows Strength / Limit / Weight, a weight bar per source (long = most weight, short and grey = the owner's view), and a shaded spotlight that moves to the source being spoken and finally to the Weight row.
  - Parallel points (strength vs limit, three sources agree, conditions that would change the judgement) use `colrule()`: a 1.5 px rule with a short accent, a label, then 52–54 px text. No half-empty boxes.
- **One focal point per shot.** On-screen text is the key phrase or number ("Perception, not measurement."), never the sentence the subtitle already shows.
- **Framing rules:** nothing within 40 px of an edge; the system diagram's overview camera is zoom 0.92 so all four nodes and the owner bar are in frame; a subline sits at least 106 px under an 84 px headline.
- **Colour:** one accent plus brick for limits. "AI share" blocks use a light tint of the accent (9DB6DD); no amber or other extra highlight colours.

## 6. Subtitles (approved style)
- Plain text, no box. IBM Plex Sans Medium 38 px, centred, vertical centre at y 948.
- Colour adapts automatically. The band luminance behind the text is measured every frame:
  - On footage: light text with a soft shadow, and the spoken word in TINT.
  - On paper: ink text, and the spoken word in ACC.
- Unspoken words in the line are at 72% opacity. There's a small spring entrance.
- Chunks are cut at clauses, merged when short, and balanced when long, with a maximum of 44 characters. Numbers display as digits (5,000 · 15% · 2.8% · 15–40%).
- **Subtitle-safe layout:** graphics must stay above y ≈ 900. The band from 920 to 980 is reserved, and the source line sits at 996.

## 6b. Main section label + source pages (added in v5, approved)
**Main section label, top-right** (`overlays.corner_label`, drawn in `render()` after the frame, before subtitles):
- Shows Introduction / Analysis / Development / Conclusion in sentence case, Plex SemiBold 26 px, right-aligned at x 1824, y 56. Under it sits a 4-segment progress bar (24 × 3 px segments) with the current step coloured.
- On paper scenes it's ACC. On footage it's TINT with a soft shadow plus a radial corner shade. Use the shot list (`footage_amount(S, t)`) to decide which, not brightness: a bright sky fooled the brightness test.
- The top-left stays for the small section labels.
- Mapping lives in `SCENE_SECTION`. The reference build used: s01–s02 Introduction, s03–s07b Analysis, s08 (answer) Conclusion, s09–s11 Development, s12 Conclusion.
- On the first scene of each heading (`FIRST_OF`), the label springs in.

**Source pages on first mention** (`overlays.doc_inset`): the first time Source A, B or C is named, the real source slides in on the right for about 5 s, then leaves.
- Sequence: about 1 s hold with the title highlighted in yellow (multiply), then one smooth sine-eased scroll down to the abstract. A light vertical motion blur scales with speed (sigma at most 3.2) so it doesn't judder at 30 fps. There's a thin scroll bar and a 24 px caption above the page, e.g. "Source A: NBER working-paper version (2023)".
- On footage, defocus the clip behind the page (`blur_footage` with `doc_window`, passed through `foot(pre=…)`) so the page never covers a face. On paper scenes, place the page where it can't touch other graphics (x ≥ 1130) and set `light=False` for a dark caption.
- Where to get the pages:
  - Working papers: NBER PDFs download fine from the sandbox (`nber.org/system/files/working_papers/wNNNNN/wNNNNN.pdf`). Run `pdftoppm -r 150` on pages 1–2 and stack them with a 40 px grey gap.
  - Pages behind a bot check (OECD): open them in the user's Chrome (Claude in Chrome), move the cursor to the edge, take full-size screenshots at each scroll step, and stitch them. Pass `url=` to get a browser bar on the inset.
  - Never complete a CAPTCHA yourself.
- Timing: the page enters about 0.1–0.2 s before the source's name is spoken and leaves before the next shot.

## 7. Automatic overlap QA (run before every full render)
- `python3 tools/video_engine/qa.py s01 … s12` draws every 2nd frame without encoding (footage is stubbed). It logs every text box and pill box, plus the corner label, then reports three things:
  - **TEXT**: two pieces of text or pills overlap.
  - **SUB**: graphics hit the subtitle line.
  - **EDGE**: text within 40 px of the frame edge. This is expected only during camera moves.
- It skips transition windows. Fix every TEXT/SUB hit, then rerun until it's clean.
- After QA, render stills at 80% through every shot (`render(sid, stills=[…])`), lay them out as 4×3 contact sheets and look at all of them. QA can't see a half-empty frame, an off-palette colour, a leftover "·" or text that's legible but ugly.

## 8. Render + finish
- `python3 build.py render s01 s02 …` writes one encoded file per scene (rawvideo pipe → libx264 veryfast CRF 18). It writes to `tmp_*.mp4` and renames only on exit code 0.
  - Run two queues in parallel on a 2-core box. The full 9.5-minute video takes about 30–40 minutes. Never render the same scene in two processes at once.
- Per scene, LEAD is 0.35 s of silence before the voice and TAIL is 0.8 s after it.
- `python3 finalize.py` pads each clip to exactly its scene's frame count. It concatenates video with `-c copy`, concatenates audio, applies loudnorm, and muxes.
- Final check: confirm the duration is between 9:30 and 10:00. Pull a frame every 6 s into contact sheets and look at all of them.

## 9. Lessons from the first builds
- Bind palette colours at call time, not as default arguments: the first palette swap left invisible text.
- Long node titles and card text need explicit 2-line wraps. Measure with `text_w` and never assume.
- Pills placed side by side need positions computed from their measured widths.
- When on-screen text repeats the subtitle line, move the graphic away from the band.
- Duration: about 1,480 words plus 13 × 1.15 s padding comes to about 9:38.
- (Build 2) Voice pace differs by voice: Alina read about 2.5 words/s over the whole script, so 1,491 words came to 10:07. Fix without re-voicing: `atempo=1.03` on every clip (keep originals in `audio/orig/`), then transcribe. Measure the first clip's pace before finalising the word count.
- (Build 2) Mixkit search pages now return a Cloudflare challenge (429). Find clip IDs with web search restricted to mixkit.co instead. Use only clips marked "Mixkit Stock Video Free License", not "Restricted". Some clips 403 at `-1080.mp4` but download at `-720.mp4`.
- (Build 2) Keep `build.py` as `import engine_core` + builders (shared BUILDERS/ORDER objects); `qa.py` and `finalize.py` import `build`. Add a soft dark band at the bottom of footage (`sub_band`) so light subtitles stay readable on bright shots.
- (Build 2) Exclude footage that contradicts the population (e.g. young children for a high-school IA).
- (v5) A stroked line of length 0 with round caps draws a dot: gate line animations on progress > 0.01, not > 0.
- (v5) Drawing a scroll at 30 fps judders without motion blur; but blur at full strength smears the page. Cap sigma.
- (v6) Bumping every headline to 84 px with a regex also caught two stacked footage lines spaced for 64 px; check line spacing after any global size change.
- (v6) A closure that reassigns a captured argument (e.g. `kick = …` inside `chapter`'s inner function) raises UnboundLocalError; use a new local name.
