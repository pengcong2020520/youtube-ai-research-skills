---
name: youtube-podcast-deep-analysis
description: Incrementally collect the newest public YouTube transcripts for a named creator or the built-in high-quality AI podcast collection, then turn unanalysed episodes into long-form Chinese first-principles deep readings and save both transcripts and analyses as Obsidian-compatible Markdown. Use when Codex needs to run the complete YouTube podcast research workflow, update a local transcript archive without duplicates, analyse existing transcript notes one episode at a time, or keep an English and Chinese AI information repository current. Never download video or audio.
---

# YouTube Podcast Deep Analysis

Run a single controlled pipeline: acquire captions, identify episodes without analyses, understand each complete transcript, write an article-quality Chinese deep reading, and audit it before delivery. Preserve depth by processing one episode at a time.

## Load the writing contract

Before drafting any analysis, read both:

- [references/analysis-template.md](references/analysis-template.md) for the exact article architecture and metadata contract.
- [references/quality-rubric.md](references/quality-rubric.md) for reasoning, coverage, editing, and rejection criteria.
- [references/ai-terminology.md](references/ai-terminology.md) for mandatory English-to-Chinese AI terminology.

Read [references/ai-sources.json](references/ai-sources.json) only when using or changing the built-in source collection.

## Resolve the request

Support three modes without asking when the user's wording is clear:

1. **Full pipeline:** fetch incrementally, then analyse only episodes without an analysis.
2. **Collection only:** fetch transcripts and stop. Do not summarise them.
3. **Analysis only:** analyse supplied or already-saved transcript notes without contacting YouTube.

Use the repository the user names. Otherwise use the active workspace. Write transcripts under `逐字稿/<creator>/` and analyses under `分析/<creator>/`.

## Acquire transcripts safely

Resolve `SKILL_DIR` to the directory containing this file. For a creator, handle, channel URL, or channel ID, run:

```bash
bash "$SKILL_DIR/scripts/fetch.sh" "<creator>" --limit 10 --output-root "<repository>"
```

For the built-in personal AI collection, run:

```bash
bash "$SKILL_DIR/scripts/fetch.sh" --collection ai-high-quality --limit 10 --jobs 3 --output-root "<repository>"
```

Use `--only <source-id>` to restrict a collection. Use `--dry-run` to preview. Parse the final JSON and retain the created paths, skipped IDs, and failures.

The skill bundles its own public-caption extractor and uses a private cache under the user's cache directory. It never downloads media. It does not install packages by default; after the user explicitly authorises the first-run installation, set `YTPDA_ALLOW_INSTALL=1` for that invocation so the wrapper can prepare `yt-dlp` and Defuddle in the private cache. If a caption track is inaccessible, leave the video out of the index and report it as retryable. Do not start audio transcription or install another tool unless the user explicitly reauthorises that expansion.

## Select pending episodes

After acquisition, build the pending list:

```bash
python3 "$SKILL_DIR/scripts/inventory.py" --root "<repository>" --creator "<creator>" --limit 10
```

Omit `--creator` to inventory all creators. Deduplicate transcript and analysis notes by YouTube video ID, not by title. Prefer the newly created transcript paths from the fetch summary, then include older pending notes if the user asked to catch up. Never overwrite an existing analysis silently; revise it only when explicitly requested.

## Understand one complete transcript

Process one episode from start to finish before opening the next one.

1. Read the YAML and the entire `## 逐字稿` body. For a long file, read consecutive ranges until EOF; do not infer the whole from its opening or from chapter labels.
2. Build a private coverage map of the central question, participants, major claims, evidence, causal transitions, disagreements, examples, promotions, digressions, and high-signal source terminology. This map is working material and must not appear in the article.
3. Identify the smallest durable problem beneath the episode. Derive 6–9 non-overlapping viewpoint pillars from causes and constraints, not from the programme's chronological order.
4. Separate speaker claims, predictions, and marketing numbers from durable conclusions. Preserve useful uncertainty inside natural prose; do not add editorial disclaimers or a fact-check appendix.
5. Remove ads, repeated anecdotes, biography, cooking, banter, and time-coded programme structure unless they change the argument.

Do not compress because the transcript is long. If context is tight, continue reading and writing in sequential passes while maintaining the same article file and coverage map.

## Write the deep reading

Write in Chinese as a complete content article, following `references/analysis-template.md`.

Use this causal unit for every viewpoint chapter:

```text
chapter claim
→ one-line 推演主线 with at least four causal steps
→ 哲学原点
→ one-sentence 最小命题
→ connected explanation of why each step leads to the next
→ a concrete landing in system, product, organisation, or practice
```

Make paragraphs carry the reasoning. Use bold paragraph leads only at genuine starts, turns, or landings; avoid converting the body into isolated bullets. A reader should be able to see both the global causal spine and the local derivation without reading process notes.

Name the output:

```text
<repository>/分析/<creator>/<creator> - <YYYY-MM-DD-or-日期未知> - <concise-Chinese-title> [<video-id>] - 深度解读.md
```

Use `analysis_status: "complete"`. Preserve the source video ID, URL, source title, and an Obsidian link to the transcript.

## Audit and revise

Run the deterministic gate after every article:

```bash
python3 "$SKILL_DIR/scripts/audit_analysis.py" "<analysis.md>" --transcript "<transcript.md>"
```

For calibration against an established corpus, add:

```bash
python3 "$SKILL_DIR/scripts/audit_analysis.py" "<analysis.md>" \
  --transcript "<transcript.md>" --reference-dir "<repository>/分析"
```

Treat structural errors and forbidden process language as failures. Treat length and density as calibration signals, never as permission to pad. After the script passes, perform the manual semantic checks in `references/quality-rubric.md`: full-transcript coverage, non-overlapping pillars, valid causal transitions, genuinely derived insights, and a useful action framework. Revise and rerun until both checks pass.

Finish with a terminology and language-cleaning pass. Apply `references/ai-terminology.md`; in particular retain `Agent`、`Agentic`、`Coding Agent`、`多 Agent` and `Agent harness`, rather than translating them as “代理” compounds. Remove stray untranslated connective words, duplicated spaces, placeholders, and unnecessary process prose while retaining established technical terms whose English form is clearer.

## Report the outcome

Give a compact handoff containing:

- created and skipped transcript counts;
- analysed and already-analysed counts;
- failed or captionless video IDs that remain retryable;
- clickable absolute paths to every new analysis and transcript;
- the final audit result.

Do not claim success merely because files exist. Completion requires a passing audit and a manual comparison to the writing contract.
