---
name: "ia-demo-video"
description: "Make a 9:30–9:55 IB Digital Society IA presentation video (MP4) from an IA PDF. It copies the style of an example video, uses a hybrid of real stock footage and motion graphics, an ElevenLabs voice, subtitles and real source pages. Use for /ia-demo-video."
---

# IA demo video (IB Digital Society)

Builds a finished IA presentation video for Criteria C, D and E as one MP4 (no Canva). It's self-contained: every IA rule is in `references/` and every tool is in `scripts/` (both relative to this skill's base directory). A chat with no project files can run it end to end.

Read these before Step 4:
- `references/ia_guidelines.md`: IA rules, the C/D/E checklist, house rules and the scene plan.
- `references/video_pipeline.md`: the exact production pipeline, numbers and lessons.
- `references/voice_rules.md`: how to write the narration.
- `references/reference_video_breakdown.md`: how to analyse the example video.

If `references/` or `scripts/` is missing (an account copy saved without its files), use the user's DS project instead. Get the engine from `tools/video_engine/` and the rules from `claude/VIDEO_IA_Demo_Pipeline.md`, `claude/00_SYSTEM_MASTER_REFERENCE.md`, `sources/IA/IA_05_Checklist_Outline_Video_C_D_E.md` and `tools/VOICE_Preservation_Protocol.md`, via the Projects tool. Failing that, ask for the shared `ia-demo-video.skill` package.

**Working style for the whole run:**
- Keep a task list, and put a time estimate in brackets in every task title, e.g. "Render all scenes [~35 min]". Update it as each step finishes.
- Send drafts and demos as soon as they're useful.
- Never spend paid credits (ElevenLabs) before the user has approved the script.

---

## Step 0: Model gate (do this before anything else)
This build needs the strongest reasoning setting: it involves frame-by-frame style analysis, a long criteria-bound script, and code that renders about 17,000 frames.
1. Check which model you are, from your own system context. If you are **not Claude Opus 5.5** (`claude-opus-5-5`), stop. Tell the user, in one short paragraph, that this skill requires Opus 5.5 at High effort or above. Ask them to switch models in the model menu and start again. Do nothing else.
2. You can't see your effort setting, so ask with AskUserQuestion: "This video build needs Claude Opus 5.5 on High (or Max) effort. Is that what you're on?" Options: "Yes, Opus 5.5 High or Max" / "Not yet, I'll switch". Continue only on the first answer. Otherwise tell them where to change it (model menu → Opus 5.5 → effort High) and stop.

## Step 1: Ask for an example video (the style reference)
Ask the user to attach an **example motion-graphics video as an MP4** whose look they want, for example an explainer or promo they like. Say what you'll do with it: measure it frame by frame and copy only its motion and design grammar, never its content or branding. Always use a **hybrid** of motion graphics and real stock footage, whatever the example does.
- If they have no example, suggest they find one (a 15–60 s product explainer works best) and wait. Use the house style (`references/video_pipeline.md` §5) only if they say explicitly that they want to skip this step.

## Step 2: Break the example down and match it to our system
Follow `references/reference_video_breakdown.md` exactly:
1. Run `python3 scripts/analyze_reference.py example.mp4 ref_analysis`.
2. Look at **every** contact sheet and keyframe, and pull consecutive frames for fast moves.
3. Write the full breakdown, all 12 headings, in this order: measured fact → why it's done → how it correlates with the rest → how our engine reproduces it.
   - Cover rhythm, transitions, easing curves in frames, typography and hierarchy, the on-screen language system, colour, layout grid, footage use, data style, texture, the rules that tie everything together, and a translation table.
   - The table must show what changes for an educational IA video: calmer timing, a readable hold of at least 1.5 s, cuts on sentence ends, no music, subtitles kept clear, citations on every evidence shot.
4. Send the breakdown in the chat (tables, concise), save it as a file next to the project, and ask the user to confirm or adjust it before going on.

## Step 3: Pick the colour palette
Build a preview image with six rows. Each row has the swatches plus a mini title card: a BG card with a TXT headline and an ACC kicker.
- **0** comes from the example video: from `ref_analysis/palette.json`, cleaned by eye into BG, SURF, TXT, MUTE, GRID, ACC, NEG, BAR, LIGHT and TINT, with ACC kept as the example's single accent.
- **1–5** are the house palettes in `references/palettes.json`:
  1. Paper + Ink Blue
  2. Graphite + Amber (dark)
  3. Chalk + Forest Green
  4. Midnight + Mint (dark)
  5. Sand + Deep Teal

Send the image with SendUserFile, ask "Reply 0–5", and wait.

## Step 4: Ask for the IA
Ask for the IA (IPD) PDF if it isn't attached, then read it in full. Extract:
- the exact inquiry question;
- the real-world example;
- the 3Cs with their codes;
- the digital system and how it works;
- the three Section B sources (authors, year, method, key numbers, limits);
- any extra sources;
- findings, the answer, limitations, and the trends or future developments.

Never invent numbers. Anything the video needs that the PDF lacks (for example a D development with evidence) must be researched with web search and cited. Tell the user what you added.

## Step 5: Ask for the ElevenLabs voice
Load the ElevenLabs tools with ToolSearch (`creative_list_voices`, `creative_create_flow`, `creative_generate_speech`, `creative_get_generations`). If the ElevenLabs connector isn't connected, suggest connecting it with SearchMcpRegistry and SuggestConnectors, then wait.

Call `creative_list_voices`, then ask with AskUserQuestion which voice to use: up to 4 options, the user's own cloned voices first. They can type another.

## Step 6: Workspace
- Create a project folder (the working directory) with `script/ audio/ words/ stock/raw stock/prep docs/ scenes3/ stills/ out/`.
- Copy everything from `scripts/` into it. Set `IA_VIDEO_ROOT` to that folder (the default is the current directory).
- Install what's missing: `pip install --break-system-packages skia-python faster-whisper numpy pillow`. You also need ffmpeg, pdftoppm (poppler) and tesseract (optional). If `import skia` fails with `libEGL.so.1`, run `apt-get install -y libegl1`. Inter fonts must be in `/usr/share/fonts/opentype/inter/`; if they're missing, download Inter from its GitHub release and point `lib.FONT_DIR` at it.
- Apply the chosen palette:
  - Replace the constants at the top of `v3style.py`: BG, SURF, TXT, MUTE, GRID, ACC, NEG, BAR, LIGHT, TINT.
  - In `subs.py`, set INK = TXT and ACC = ACC. Keep TXT/CUR = LIGHT/TINT for footage.
- Apply the example's motion settings from the Step 2 translation table (spring durations, stagger, transition lengths, type sizes).

## Step 7: Script, then wait for approval
Write `script/scenes.json` as a list of `{id, section, text}`, following `references/ia_guidelines.md` §6 (13 scenes, about 1,480 words, including s07b "Weighing the evidence") and every checklist line in §2.

House rules:
- Name the sources Source A/B/C, never 1/2/3.
- Attribute every claim aloud ("According to Source C, …"), and introduce illustrations with "for example".
- Write numbers as words.
- The C answer comes before D, and D is a labelled section.
- Follow the teacher voice in `references/voice_rules.md`: run the drift check and remove any stock phrases.
- Never reuse topics or content from sample IA/EE files.

Show the user the whole script and **wait for approval**, because voicing costs credits. Save it as a script document; in the DS project, that's `claude/IA_Demo_Video_Script_<topic>.md`.

## Step 8: Voice and timing
1. Call `creative_create_flow` once. Then, for each scene, call `creative_generate_speech` with the chosen voice, model `eleven_v4` and `generations_count: 1`. **Never call a generation again to retry**, because every call is charged.
2. Get each `full_res_url` from `creative_get_generations` and `curl` it to `audio/<sid>.mp3`.
3. Measure the pace of the first clip. If the total would pass 9:55, apply `atempo` of about 1.03 to every clip (keep the originals) rather than cutting content. If it would be under 9:30, raise TAIL or add content.
4. Run `python3 transcribe.py <ids>`.
   - Diffs that are only spelling variants are fine.
   - If words are "missing", re-transcribe that ±2 s window. If the words are in the audio, patch `words/<sid>.json`.
   - Re-voice only if words are truly absent.

## Step 9: Stock footage (real, never AI)
- Use Mixkit. Its search pages may be behind a bot check, so find clip IDs with web search restricted to mixkit.co. Use only clips marked with the free licence.
- Run `sh prep_footage.sh <id> <name>` for about 12–14 clips that match the IA's setting and population. If `-1080.mp4` returns 403, use `-720.mp4`.
- Don't use footage that contradicts the population (for example, young children in a high-school IA).
- Remind the user to check the licence.

## Step 10: Source pages for first mentions
For each of Source A, B and C, get the real source:
- **Open PDFs (NBER, arXiv, university pages):** download with curl, run `pdftoppm -r 150` on pages 1–2, and stack them with a 40 px grey gap into `docs/srcX_strip.png`. Note the title box in pixels for the highlight.
- **Pages behind a bot check (e.g. OECD):** open them in the user's Chrome (Claude in Chrome). Move the cursor to the edge of the page, take full-size screenshots with `save_to_disk` at each scroll step, and stitch them. Pass `url=` so the inset shows a browser bar.
  - **Never solve a CAPTCHA:** ask the user to pass it in their Chrome, then continue.
  - If nothing works, use a clearly labelled retyped title card ("retyped title page · original at …").
- Caption honestly, e.g. "Source A · NBER working-paper version (2023)", and keep the on-screen source line for the published version.

## Step 11: Build the scenes
Copy `build_template.py` to `build.py`. Set `ORDER`, `overlays.SCENE_SECTION` and `FIRST_OF` (Introduction / Analysis / Development / Conclusion; the answer scene goes under Conclusion), then write one `build_<sid>(S)` per scene.
- **Key every animation to a spoken phrase with `S.T("exact phrase")`.**
- **Hybrid:**
  - Alternate full-bleed footage shots (`foot()`) with flat motion-graphics shots (cards, bars, rings, a camera-driven system diagram, `statement()`, `chapter()`), as the example's grammar dictates.
  - Cut every 4–8 s on sentence ends.
  - Add a slow push on every shot.
  - Use the transitions the breakdown chose.
- The C2 system explanation uses a labelled diagram: input → processing → output → human, plus who controls it. Highlight the node being explained, and include a "for example".
- Every evidence shot gets a source line (y 999).
- Keep graphics above y ≈ 900 so the subtitle band (920–980) stays clear.
- The first mention of each source gets `doc_inset`:
  - Show it for about 5 s: about 1 s holding on the yellow-highlighted title, then one smooth sine-eased scroll to the abstract, with light motion blur.
  - On footage, add `pre=blur_footage…` so the page never covers a face.
  - On paper scenes, place it at x ≥ 1130 with `light=False`.
- The top-right main heading (with its 4-step progress bar) and the subtitles are drawn automatically by `render()`. Keep the top-left for small section labels.

Subtitle spec (approved):
- plain text with no box, Inter Medium 38 at y 948;
- light text with a soft shadow on footage, ink text on light scenes (switches automatically);
- the spoken word tinted, unspoken words at 72%;
- lines of up to 44 characters, balanced at clauses;
- numbers shown as digits.

## Step 12: 10-second style demo (checkpoint)
Render about 10 s that show the style: an evidence scene with footage, a source-page inset, subtitles, the corner heading and one graphic. Use `subdemo`-style code: `draw_frame` + `corner_label` + `draw_subs` + grain + audio trimmed from the clip.

Send it and ask whether the style, palette, subtitles and pacing are right. Iterate on demos until the user approves.

## Step 13: QA, render, deliver
1. Run `python3 qa.py <all ids>`. Fix every TEXT and SUB hit; EDGE is fine only during camera moves. Rerun until it's clean.
2. Render stills at the busiest moment of every shot and look at them. Fix card, pill and dot collisions, which QA can't see.
3. Run two background queues: `python3 build.py render …`. This takes about 30–40 min on 2 cores. Keep the task list estimate updated.
4. Run `IA_VIDEO_OUT=out/<topic>.mp4 python3 finalize.py`. Check the length is 9:30–9:55 and that the audio and video durations match.
5. Pull a frame every 6 s into contact sheets and review **all** of them. Fix anything, re-render only the affected scenes, and finalize again.
6. Deliver the MP4 with SendUserFile.
7. Save the script doc with the Source A/B/C mapping, footage IDs and credits.
8. Remind the user:
   - add every presentation source to the IPD reference list;
   - check the footage licence;
   - if the IPD numbers its sources 1–3, it should match the A/B/C used in the video;
   - in a student's own submission, they must write the script themselves and acknowledge AI use.