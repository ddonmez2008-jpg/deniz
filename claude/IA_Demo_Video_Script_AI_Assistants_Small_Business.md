# IA demo video: final script (v4)

> Teacher exemplar presentation for the IA on generative AI assistants in small businesses. Voice: ElevenLabs, cloned "Bugra Buyukduykular" voice. Length 9:38 (limit 10:00). Subtitles throughout.

**Source naming in the video:** Source A = Brynjolfsson, Li & Raymond (2025), Source B = OECD (2025), Source C = Humlum & Vestergaard (2025). Every claim is attributed aloud ("According to Source C…"). Extra presentation sources are named by author ("According to Noy and Zhang…").

**Note:** the IPD numbers its sources 1–3. If students copy this format, the IPD headings should use Source A/B/C too, so the video and IPD line up.

**Style:**
- Paper + Ink Blue palette, Inter Display type.
- Real stock footage from Mixkit as full-screen cut scenes.
- Motion graphics with spring motion and overlapping word reveals.
- Zoom-through and cross-dissolve transitions, with motion blur on fast moves.
- An on-screen source line on every evidence shot.
- Plain word-timed subtitles: light text on footage, ink text on paper, with the spoken word highlighted.
- No music.

How it was built: see `claude/VIDEO_IA_Demo_Pipeline.md`.

## 0:00 · Inquiry focus

To what extent do generative AI assistants that automate repetitive office tasks affect productivity and employment in small businesses? According to Microsoft's announcement in January 2024, Copilot for Microsoft 365 no longer needs a three-hundred-licence minimum. Suddenly, a business of ten people could use the same assistant as the Fortune 100. But the announcement said nothing about productivity, and nothing about jobs. That gap is what this inquiry investigates, through the economic context, artificial intelligence, and the concept of change.

*Footage:* office (Mixkit 914), meeting (Mixkit 4804)

## 0:36 · How the digital system works

First, how the system works. The input is a user's prompt, plus company data: emails, chats, documents and meetings. Copilot passes these to a large language model, which predicts the most likely words to come next. The output is a draft, a summary or an answer, inside Outlook, Word, Excel or Teams. For example, an owner can ask Copilot to summarise a long email thread, and it returns the key points and a draft reply in seconds. An employee decides whether to use it, and the owner controls the licences and which data the tool can see. The key part of this mechanism is prediction. The model is strong where language is predictable and repetitive, but it cannot check whether its own output is true. So the impact should depend on the task.

## 1:24 · Analysis · Theme 1: productivity on a single task

Theme one: productivity on a single task. The strongest causal evidence is Source A, by Brynjolfsson, Li and Raymond. According to Source A, when five thousand customer support agents gained an AI assistant at different times, issues resolved per hour rose by fifteen percent on average, by around thirty percent for less experienced agents, and hardly at all for the most skilled. According to Noy and Zhang's experiment, writing tasks took forty percent less time, and quality rose by eighteen percent. The model has learned what good answers look like, so it passes the habits of top workers on to new ones. That matters for small firms, which often hire untrained staff.

*Footage:* call centre (Mixkit 23064), typing (1781), support agent (9159)

## 2:07 · Analysis · Theme 1 qualified

But this needs qualifying. Both studies measure one repetitive task, and the support firm in Source A trained its assistant on its own huge archive of past conversations. A ten-person firm has far less data. According to Dell'Acqua and colleagues, there is a second limit. Consultants using GPT-4 completed twelve percent more tasks, twenty-five percent faster, when the task was inside the AI's capability. On a task outside it, they were nineteen percentage points less likely to reach the right answer. This links back to the mechanism: the model predicts plausible text, it does not check it. So task-level gains are real, but they are a ceiling, not a typical result.

*Footage:* office (914, mirrored)

## 2:50 · Analysis · Theme 2: productivity across the whole job

Theme two: productivity across a whole working week. Source C, by Humlum and Vestergaard, linked surveys of twenty-five thousand Danish workers to official records of their earnings and hours. According to Source C, chatbot users saved only two point eight percent of their working time, with no measurable effect on earnings or hours. Why so different from Source A? A week contains many tasks, and only some are predictable enough for the model. For example, saving forty percent on a quarter of your work is not the same as saving forty percent of your job. I find Source C more persuasive for the whole job, because it uses administrative records rather than opinions. But it is still a working paper, and it does not separate small firms.

*Footage:* accounts (4533)

## 3:37 · Analysis · Theme 2: the owner's perspective

The owner's perspective comes from Source B, the OECD's survey of over five thousand small and medium-sized firms in seven countries. According to Source B, thirty-one percent had adopted generative AI, and around a third of those reported less workload for staff or the owner. This supports a time-saving effect, but it is perception, not measurement. According to Otis and colleagues, owners' experiences can differ a lot. When Kenyan entrepreneurs were given a GPT-4 business mentor, high performers improved by about fifteen percent, but low performers did about eight percent worse. The difference came from which advice they chose to act on. So the same tool can widen the gap between strong and weak small businesses.

*Footage:* shop worker (48714), papers (45923)

## 4:24 · Analysis · Theme 3: employment

Theme three: employment. According to Source B, eighty-three percent of adopters reported no change in staff numbers, nine percent a reduction, and six percent an increase. Source C agrees, with no measurable change in hours or earnings. And according to Source A, new agents with the assistant were less likely to quit. Three methods, three stakeholder groups, and the same direction: jobs are being reorganised rather than replaced. There are two qualifications. Owners may not notice a job that was simply never advertised. And according to Source B, fourteen percent of adopters used fewer contractors. So part of the employment effect may fall outside the firm, on freelancers who never appear in a staff count.

*Footage:* laptop at night (17450)

## 5:11 · Weighing the evidence (new in v4)

Before answering, I need to weigh the three sources against each other. Source A has the strongest design, because the assistant reached agents at different times, so the change can be linked to the tool. But it comes from one large firm, with years of its own data. Source B is the only source built around small firms, and it covers seven countries, but it records what owners believe, not what happened. Source C uses official records, so it does not depend on opinion, but it does not split results by firm size. So I give Source A the most weight for single tasks, Source C for the whole job, and Source B for the owner's view.

*On screen:* three source cards, each showing its strength (tick), its limit (cross), and the weight given to it.

## 5:52 · Answer to the inquiry question

So, to answer my question. Generative AI assistants raise productivity strongly on single, repetitive, language-based tasks, by roughly fifteen to forty percent. Across the whole job, the effect so far is small: under three percent of working time. For employment, the main effect is a change in what people do, not in how many people are employed, but contractors may lose work. The strongest evidence for this is Source C, because its administrative data does not rely on what owners believe. The main limitation is that none of my sources isolates businesses with fewer than fifty employees, and all of them cover only the first two years of adoption. So this answer applies to small businesses in high-income economies, so far.

*Footage:* remote worker (4957)

## 6:39 · Development 1: assistants to agents

Emerging trends and future developments. The first development is the move from assistants to agents: AI that completes multi-step tasks without a person checking each step. Xu and colleagues built TheAgentCompany, a simulated small software firm with one hundred and seventy-five office tasks. According to their results, the best agent completed about thirty percent of them on its own. That is a measured result, but in a simulation, and the paper is a preprint. If agents improve, the mechanism changes. A person no longer reviews every output, so whole-job savings could move closer to the task-level gains in Source A. But the jagged frontier warns that unchecked errors would grow too, and in a small firm there is often nobody else to catch them. So my employment judgement could shift from reorganised towards replaced, but only for the most predictable tasks.

*Footage:* data network (31771)

## 7:36 · Development 2: the size gap in adoption

The second development is the size gap in adoption. According to Eurostat's 2025 data, twenty percent of EU enterprises used AI, up six and a half points in one year. But that was only seventeen percent of small enterprises, compared with fifty-five percent of large ones. Evidence from France shows why this matters. According to Acemoglu, Lelarge and Restrepo, manufacturing firms that adopted robots grew, but at the expense of their competitors, and industry employment fell overall. That was robots, not generative AI, so the comparison is limited. But if the pattern repeats, the biggest employment effect on small businesses may come not from adopting AI, but from not adopting it when competitors do.

*Footage:* shop worker (48714, mirrored)

## 8:23 · Development 3: the productivity J-curve

The third development is the productivity J-curve. According to Brynjolfsson, Rock and Syverson, general purpose technologies first need hidden investment in training and new ways of working, so measured productivity can stay flat, or even dip, before it rises. This could explain why Source C shows so little after two years. It is a theory, not a measurement for generative AI, so it cannot prove that gains will come. But it means my finding of small whole-job effects may describe the bottom of the curve, not the final result.

## 8:56 · Closing insight

So what does the future-facing evidence add? It shows that my answer depends on time, and on who checks the output. Today, AI is reorganising small-business work rather than replacing it. This also matters beyond business. If small firms adopt more slowly than large ones, as the Eurostat data shows, the gains may flow to firms that are already strong, and the gap between them could widen. That makes it a question of equity as well as efficiency. My judgement would change if long-term administrative data, split by firm size, showed hours or staff falling, or if agents proved reliable without human checking. That is the evidence I would look for next.

*Footage:* call centre (22987). *On screen:* an illustrative chart of the large-firm and small-firm gains gap, labelled Concept 2.7 Values and ethics.

## Media credits

Stock footage: Mixkit (mixkit.co); clip IDs are listed above. Check the Mixkit licence before sharing. Voice-over: ElevenLabs text-to-speech. All charts and diagrams are original, drawn from the data cited on screen.
