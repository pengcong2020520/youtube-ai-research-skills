# YouTube 主题来源选择规范

## Selection objective

Choose sources that collectively improve understanding of the exact topic. Popularity helps discover socially important material; it does not establish accuracy or depth.

## Automatic shortlist signals

The bundled search script combines:

- keyword coverage in title and description;
- YouTube search rank;
- total views and views per day;
- like and comment engagement when available;
- publication recency;
- long-form duration;
- channel audience as a modest authority prior;
- small positive signals for interviews, research, benchmarks, experiments, engineering, and technical discussion;
- small penalties for generic listicles, exaggerated promises, and purely promotional course titles.

The score is intentionally bounded so that one viral metric cannot dominate all other considerations.

## Editorial source tests

Retain a video only when it passes all applicable tests:

1. **Direct relevance:** its central subject answers the supplied keyword, not just a passing mention.
2. **Information density:** it contains mechanisms, evidence, experience, or a substantive argument.
3. **Source identity:** the speaker's role and incentive can be understood well enough to interpret claims.
4. **Traceability:** important factual or numerical claims have an identifiable origin, even if that origin still needs verification.
5. **Independence:** it is not merely repeating the same underlying press release, interview, benchmark, or paper as another selected video.
6. **Completeness:** captions cover enough of the video for full analysis.

## Portfolio composition

Require at least three channels and normally select five videos. Prefer at most one video per channel.

When the topic supports it, seek complementary roles:

- a primary researcher, founder, builder, or first-hand practitioner;
- an independent technical explainer;
- a deployment or operations perspective;
- an evaluator, critic, or skeptical practitioner;
- a long-form interviewer who exposes assumptions and tradeoffs.

Do not add a weak “opposing” source merely to create symmetry. A well-supported qualification is more useful than performative balance.

## Recency versus durability

- Use recent videos for fast-moving products, model releases, policy, pricing, benchmarks, and market structure.
- Set `--recency-days 0` for conceptual, historical, scientific, or philosophical topics where older canonical explanations may be stronger.
- When a recent video relies on an older primary talk or paper, prefer retaining both only if they play different evidentiary roles.

## Independence levels

Classify source relationships privately:

- **Independent primary:** different teams or observations produce compatible evidence.
- **Independent interpretation:** different analysts reach similar explanations from separate reasoning.
- **Shared origin:** several videos repeat one paper, benchmark, press release, demo, or anecdote.
- **Direct disagreement:** sources make incompatible factual or causal claims.
- **Different scope:** claims appear inconsistent but concern different populations, tasks, time horizons, or definitions.

Only the first two strengthen corroboration. Shared-origin repetition strengthens visibility, not truth.
