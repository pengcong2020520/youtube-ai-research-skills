---
name: youtube-topic-research-analysis
description: Search YouTube by a supplied topic or keyword, rank current high-interest and high-quality long-form videos, incrementally collect transcripts from multiple independent channels, cross-validate their claims, and save one article-quality Chinese first-principles research report as Obsidian-compatible Markdown. Use when Codex needs to research a topic across several YouTube sources, compare consensus and disagreement, update a topic corpus without duplicate video IDs, or produce a multi-source deep reading instead of analysing one creator or episode. Never download video or audio.
---

# YouTube Topic Research Analysis

Turn one keyword into a source-diverse transcript corpus and one long-form Chinese research article. Optimise for useful evidence, not raw view count.

## Load the contracts

Before searching, read [references/source-selection.md](references/source-selection.md). Before synthesis, read [references/research-template.md](references/research-template.md), [references/quality-rubric.md](references/quality-rubric.md), and [references/ai-terminology.md](references/ai-terminology.md).

## Resolve the mode

Support three modes:

1. **Full research:** search, select, fetch, cross-validate, write, and audit.
2. **Corpus only:** search and fetch transcripts, then stop.
3. **Synthesis only:** use a supplied manifest or transcript set without contacting YouTube.

Use the repository the user names. Otherwise use the active workspace.

## Search and collect

Resolve `SKILL_DIR` to this skill directory. Start with the user's exact keyword. Add at most two query variants only when they improve source coverage—for example an English equivalent, `interview`, `research`, `debate`, or a specific technical synonym. Do not silently broaden the subject.

Run:

```bash
bash "$SKILL_DIR/scripts/run.sh" "<keyword>" \
  --candidates 30 --inspect 15 --select 5 --min-sources 3 \
  --output-root "<repository>"
```

Pass each extra search formulation as `--variant "<query>"`. Useful options:

- `--recency-days 730`: only accept videos published within the interval; use `0` for evergreen research.
- `--min-views 5000`: remove very low-signal candidates.
- `--min-duration 600`: exclude Shorts and brief news clips.
- `--max-per-channel 1`: prefer independent channels.
- `--dry-run`: inspect ranked candidates without writing or extracting transcripts.
- `--language zh-Hans`: preferred caption language; Defuddle may fall back.

The script combines YouTube search rank, keyword coverage, views, view velocity, engagement, duration, channel reach, and modest quality signals. Treat its score as a shortlist heuristic, never as evidence that a video is correct. Read the candidate titles, descriptions, channels, and selection reasons before accepting the corpus.

The script never downloads media. It does not install tools by default; after the user explicitly authorises the first-run installation, set `YTTOPIC_ALLOW_INSTALL=1` for that invocation so the wrapper can prepare `yt-dlp` and Defuddle in a private cache. It searches more candidates than needed, then keeps fetching in ranked order until it has the requested number of accessible transcripts. It deduplicates by YouTube video ID across the entire repository and reuses an existing transcript path instead of copying it.

Require at least three different channels. Prefer five sources when available. Do not continue to synthesis when `quality_gate_met` is false.

## Curate the corpus

Open the generated versioned `research-manifest-<id>.json`. Reject and replace a selected source when it is:

- only weakly related to the exact question;
- a short news rewrite, trailer, reaction, or promotional funnel with little substantive content;
- derived from the same interview, press release, paper summary, or corporate claim as another source;
- dominated by setup instructions when the topic requires explanation or evidence;
- inaccessible, truncated, or too repetitive to support analysis.

Aim for role diversity when the topic permits: primary researcher or builder, independent practitioner, technical explainer, skeptical evaluator, and long-form interviewer. Different channels do not automatically constitute independent evidence.

If editorial review removes a source, rerun with a narrower variant, a larger candidate pool, or an explicit keyword refinement. Do not manually manufacture a balanced set from unrelated videos.

## Read every transcript and build an evidence map

Read every selected transcript completely, one file at a time and in consecutive ranges until EOF. For each source, privately record:

- its central question and conclusion;
- the speaker's role and possible incentives;
- factual claims, mechanisms, examples, measurements, predictions, and promotional assertions;
- primary evidence cited versus opinion or repeated reporting;
- claims that agree with, qualify, or contradict another source.
- source terms whose English form carries technical scope and must remain stable in Chinese.

Then create a private claim matrix:

```text
claim
→ supporting sources
→ challenging or limiting sources
→ whether sources are genuinely independent
→ evidence type and strength
→ synthesis judgment
```

Do not publish the working map. Cross-source repetition is not automatically corroboration: trace whether several videos ultimately depend on the same company announcement, benchmark, paper, or anecdote.

## Derive the report

Identify the smallest durable problem beneath the keyword. Build 6–9 non-overlapping pillars from causal mechanisms and constraints, not one chapter per video.

For each pillar:

1. state a conclusion;
2. write a `推演主线` with at least four meaningful transitions;
3. explain the `哲学原点`;
4. compress it into one `最小命题`;
5. use connected prose to explain why every transition follows;
6. integrate supporting, qualifying, and dissenting sources naturally;
7. land in research, product, organisation, governance, or practice.

Use source names where attribution changes the meaning. Distinguish multi-source agreement from independent verification, and distinguish speaker claims from the report's judgment. Do not force consensus.

Follow [references/research-template.md](references/research-template.md). Save:

```text
<repository>/分析/主题研究/<keyword-slug>/<YYYY-MM-DD> - <Chinese-title> [topic-<research-id>] - 深度解读.md
```

Use the `research_id`, source metadata, and transcript links from the manifest. Never overwrite a report with the same source set silently.

## Audit and revise

Run:

```bash
python3 "$SKILL_DIR/scripts/audit_report.py" "<report.md>" \
  --manifest "<research-manifest.json>"
```

Optionally calibrate article depth against the accepted single-source corpus:

```bash
python3 "$SKILL_DIR/scripts/audit_report.py" "<report.md>" \
  --manifest "<research-manifest.json>" \
  --reference-dir "<repository>/分析"
```

Treat structural, source-diversity, metadata, and forbidden-language failures as blocking. Then complete the manual semantic gate in `references/quality-rubric.md`. Revise until both gates pass.

Finish with a terminology and language-cleaning pass. Apply `references/ai-terminology.md`; in particular retain `Agent`、`Agentic`、`Coding Agent`、`多 Agent` and `Agent harness`, rather than translating them as “代理” compounds. Remove placeholders, stray untranslated connective prose, unsupported certainty, duplicated sections, and process narration.

## Report the outcome

Report:

- keyword and query variants;
- candidate, selected, created, reused, and failed counts;
- selected channels and video IDs;
- whether the three-source diversity gate passed;
- transcript, manifest, and report paths;
- final audit score and any residual evidence limitations.

Do not claim cross-validation merely because several transcripts were collected.
