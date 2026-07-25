# 深度解读文章模板

Use this architecture as a contract, not as text to copy. Adapt chapter names and counts to the source.

## Frontmatter and filename

```yaml
---
title: "<中文主标题：副标题>"
creator: "<博主或节目>"
source_title: "<原视频标题>"
source_video_id: "<YouTube ID>"
source_url: "https://www.youtube.com/watch?v=<ID>"
source_transcript: "[[<逐字稿文件名，不含 .md>]]"
analysis_status: "complete"
analysis_method: "整体叙事、第一性原理、因果推演、观点裁剪"
created: "<YYYY-MM-DD>"
tags:
  - podcast-analysis
  - <topic>
  - first-principles
---
```

Filename:

```text
<creator> - <published-or-日期未知> - <concise-Chinese-title> [<video-id>] - 深度解读.md
```

## Article skeleton

```markdown
# <能表达最终判断的标题>

> [!abstract] 全文结论
> <一个高密度段落：问题、核心机制、主要张力、最终判断。>

## <访谈/内容>概览：<本期真正讨论的问题>

<自然说明节目、主持人、嘉宾、主题和内容范围。只写与理解有关的信息。>

### 这期节目主要讨论什么

<用 3–5 个编号问题组织概览。每一点说明问题和节目给出的关键方向。>

### 四个核心判断

<恰好四条；每条是完整判断加一句解释，不是关键词。>

### 全文逻辑主线

```text
起点
→ 中间机制
→ 新矛盾
→ 更深问题
→ 解决路径或结构变化
→ 最终判断
```

<用一个短段落解释贯穿全文的主要张力。>

## <核心观点支柱一：结论式标题>

> **推演主线：** A → B → C → D → E。

### 哲学原点：<不可再简化的认识论、因果、价值或制度原理>

<解释原点本身及其为什么适用于当前问题。>

> [!summary] 最小命题
> <一句可独立成立、可被检验、信息密度高的命题。>

**从 A 开始。** <解释 A 的具体含义和证据。>

<连续解释 A 为什么推出 B、B 为什么推出 C。每个转折都写出中间机制。>

**真正的转折在于……** <把表层主张推进到底层结构。>

**因此……** <落到产品、组织、研究或实践含义。>

<以同一结构写 6–9 个非重叠支柱；不写“第一步/第二步/第三步”。>

## 去掉<人物故事、融资、热潮、具体预测等>之后，真正留下什么

<完成观点裁剪：哪些只是载体，哪些是可迁移结构；用连贯段落写出。>

## 核心洞察：<全文结合后的深层判断>

### 洞察一：<不等于前文复述的新判断>

<由至少两个支柱交叉推出，写清推导。>

<共 5–8 条洞察。>

## 面向实践者的行动框架

### 1. <动作标题>

<动作、原因、可观察完成标准。>

<共 6–10 个有顺序的动作，形成闭环而非清单。>

## 最终判断：<一句有区分度的结论>

<收束全文：重申底层机制、主要限制和真正值得下注的方向。>
```

## Layout rules

- Keep the overview skimmable with numbered questions, four judgments, and one causal spine.
- Make viewpoint chapters the dominant share of the article. Each chapter needs several connected paragraphs, not a decorated summary.
- Use lists only where the information is genuinely parallel: overview questions, four judgments, and the action sequence.
- Keep programme timestamps, segment schedules, and transcript-processing remarks out of the article.
- Prefer precise plain language. Retain necessary English technical terms at first use when translation would blur meaning.
- Apply `ai-terminology.md` consistently. In AI contexts write `Agent`、`Agentic`、`Coding Agent` and `多 Agent`, never “代理式”“编码代理” or “多代理”.
