# VOICE — Preserving the student's voice in feedback and model examples

> Goal: every example, model sentence or edit the system gives a student sounds like **that student at their best**: their vocabulary level, sentence rhythm and connectives. It should not read as generic polished prose. Natural, specific, plain academic writing is also simply better quality.
> Tool: `tools/voice_profile.py` (standard-library Python; `report`, `profile`, `drift` modes).
> **Default mode (set by the user): TEACHER VOICE.** The user generates the examples for their students, so all examples, model paragraphs and handouts are written in the **teacher's** profile: `profiles/teacher_voice_profile.md`.
> Optional student mode: `students/<code>/voice_profile.md` (code, not name), used only if the teacher asks for feedback in a specific student's voice.

## 1. Build the profile (teacher profile first; student profiles optional)
1. Collect **≥ 500 words (ideally 1,500+) of the writer's own unassisted writing**. Teacher: worksheets, feedback comments, emails, articles or model answers written without AI. Student: in-class writing or an earlier draft. Not text already edited by AI. Mixed genres give a truer profile.
2. Run `python3 voice_profile.py report sample.txt` and save the report plus `profile` JSON.
3. Add a short human read underneath (5 lines max): typical sentence shapes, favourite connectives, how they hedge, preferred person (I / impersonal), recurring **errors** (these get fixed, not preserved).
4. Store it as `students/<code>/voice_profile.md`.

Key numbers to respect: mean sentence length, % long sentences, % 3+ syllable words, connectives they actually use, hedge and booster rate, passive rate, first-person use.

## 2. Edit levels (the system always says which level it is using)
| Level | What the system does | Wording rule |
|---|---|---|
| **0 Comment** | Flags the issue and quotes the criterion; no rewrite. | — |
| **1 Light fix** | Spelling, grammar, citation format, wrong code, word-count trims. | Keep the student's words; change only what is wrong. Target **≥ 85% word retention**. |
| **2 Model in their voice** | A short model (1–3 sentences) showing *the move* (e.g. "explain what the source cannot establish"). | Uses only the student's vocabulary range and connectives. No stock phrases. Sentence length within ±20% of their mean. |
| **3 Generic teaching example** | A full model paragraph for the class. | Written on **placeholder content** (Tool X, School X, Source 1, fictional figures in brackets), as in IA_02. It teaches the structure but cannot be pasted into a real IA/EE. |

Default for individual student feedback: **Level 0 + Level 2.** Level 1 only when requested. Level 3 for class handouts.

## 3. Drift check before anything is sent
For any Level 1–2 text, run `python3 voice_profile.py drift students/<code>/profile.json original.txt edited.txt` and fix the text if:
- any **stock phrase** is introduced ("it is worth noting", "pivotal", "underscores", "delve", "plays a crucial role", "navigate the complexities", "fostering", "moreover" when the student never uses it…);
- a **connective** appears that the student never uses;
- mean sentence length or the long-word % shifts beyond tolerance;
- several **new words** appear that are above the student's level (swap them for words the student already uses).

## 4. Writing rules for all examples (even without a profile)
- Concrete over abstract: name the system, the group, the number, the source. Specific detail is what makes writing sound like a real person thinking.
- Vary sentence length the way the student does; don't make every sentence the same shape.
- Prefer the student's own connectives ("but", "so", "because", "also") over formal stacks ("Moreover… Furthermore… Nevertheless…").
- One idea per sentence; no decorative adjectives; no throat-clearing openers.
- Use DS terminology accurately (the criteria reward it), at the level the student can explain in the viva voce.

## 5. Integrity (part of the design)
- Examples model **reasoning and structure**. The student writes their own sentences. Level 3 examples use placeholder content for exactly this reason.
- The system does **not** promise, test for or optimise against AI-detection tools. Its aim is natural, student-level, good-quality writing. No detector result can be guaranteed either way.
- Under IB policy, AI-generated text placed in submitted work must be identified and referenced, however natural it sounds. If a student adopts edited wording, it goes in their AI-use log. Authenticity is also checked in the EE viva voce.
