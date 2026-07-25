# 深度解读质量规范

## 1. 全局理解

An article passes only when it reflects the complete transcript rather than a topical sample.

- Cover the central question, the argument's starting assumptions, every major turn, important evidence, and the ending position.
- Reorganise chronology into a causal structure, but do not erase a late-stage claim merely because it does not fit an early outline.
- Identify host and guest when the source makes them clear. When it does not, write only what is known; never add a meta sentence explaining the omission.
- Exclude advertising, repeated examples, biography, banter, and production details unless they change a conclusion.

## 2. First-principles pillars

Use 6–9 pillars for a substantial long-form episode. Fewer pillars often compress distinct mechanisms; more often fragments one mechanism into headings.

Each pillar must satisfy all five tests:

1. It states a durable conclusion, not a topic label.
2. Its philosophical origin is an actual underlying principle—causal inference, bounded rationality, verification, agency, incentives, path dependence, institutional trust, or another source-specific principle.
3. Its inference line contains at least four meaningful steps.
4. The prose explains why each transition follows; arrows alone are not an argument.
5. Its scope does not substantially duplicate another pillar.

The `最小命题` is a one-sentence compressed claim. It is not a slogan and should remain meaningful when quoted alone.

## 3. Evidence and epistemic discipline

- Distinguish what the speaker reports, predicts, sells, or speculates from what the article concludes.
- Do not silently turn a guest's numerical claim into an established fact.
- Do not fabricate participants, company roles, study results, or causal evidence.
- Keep uncertainty in the relevant paragraph. Avoid generic warning boxes, fact-check appendices, or process commentary.
- Use the transcript as the primary source. External sources may verify unstable facts, but they must not replace transcript understanding.

## 4. Viewpoint crop

The crop section removes source-specific packaging and preserves transferable structure.

- Name the elements being removed: publicity numbers, biography, financing, demos, timing predictions, or other episode-specific carriers.
- State what remains after removal and why it generalises.
- Do not create a generic “pros and cons”, “boundary and counterexample”, or “unanswered questions” section.

## 5. Core insights

Write 5–8 original insights. Every insight should combine at least two earlier pillars or reveal a second-order consequence. Reject an insight if it merely renames a chapter.

A strong insight follows this shape:

```text
pillar A + pillar B
→ previously hidden dependency or shifted bottleneck
→ consequence for competition, governance, product, research, or organisation
```

## 6. Action framework

Write 6–10 ordered actions. Each action needs:

- a verb-led decision or behaviour;
- a reason grounded in the article;
- an observable completion or evaluation condition.

The sequence should move from problem definition through implementation, validation, governance, and iteration. Avoid generic advice such as “关注趋势” or “持续学习”.

## 7. Readability

- Use an article's narrative voice, not a report of the analysis process.
- Use structural headings, but make paragraphs carry the logic.
- Use bold paragraph leads sparingly for starts, turns, and landings.
- Avoid one-sentence paragraph chains, excessive bullets, repetitive conclusion phrases, and ornamental jargon.
- Do not include a programme time table or timestamps.
- Remove untranslated connective prose and accidental mixed-language fragments. Keep English only for useful technical terms such as Agent, RLVR, harness, token, or benchmark.
- Follow `ai-terminology.md`. Retaining field-standard English is professional precision, not accidental mixed-language writing.
- Never use “代理式”“编码代理”“多代理”等表达 for AI `Agent` concepts; preserve `Agent` and its word family.

## 8. Forbidden scaffolding

Reject or rewrite any draft containing analysis-process headings or filler such as:

- `第一步` / `第二步` / `第三步`
- `通读全文` / `第一性原理提取`
- `把问题还原到不可简化的层次`
- `节目锚点` / `支点观点`
- `可审计的论证链`
- `边界与反证`
- `没有充分回答的问题`
- `节目时间结构`
- “逐字稿没有标注名字，因此……”
- “由于上下文限制，本文……”

## 9. Calibration against the accepted corpus

Five accepted long-form analyses established these descriptive ranges:

- 6–9 core pillars; the current examples use 7–9.
- One `哲学原点`, `推演主线`, and `最小命题` per pillar.
- 5–8 core insights; current examples use 6–7.
- 6–10 actions; current examples use 8–9.
- Accepted viewpoint chapters contain roughly 800–1,300 Unicode characters each; a chapter below 700 usually indicates an unexplained causal jump.
- Roughly 12,400–14,500 Unicode characters for 40–120 minute information-dense episodes.

These are calibration bands, not padding targets. A shorter focused episode may produce a shorter article; a longer dense episode may exceed them. No output passes solely because its counts match.

## 10. Final manual gate

Before delivery, answer yes to every question:

1. Could a reader reconstruct the episode's global argument from the overview and causal spine?
2. Did the analysis include the transcript's late-stage claims and meaningful disagreement?
3. Does every pillar derive rather than merely restate?
4. Are the pillars mutually distinct and collectively sufficient?
5. Are the insights genuinely new combinations?
6. Does the crop preserve transferable structure without flattening uncertainty?
7. Can a practitioner act and verify progress using the final framework?
8. Is every unnecessary meta sentence gone?
9. Does every high-signal AI term preserve the source's professional meaning and remain consistent throughout?
