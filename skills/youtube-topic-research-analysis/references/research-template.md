# 多源主题深度解读模板

Use this architecture as a contract. Adapt chapter names to the topic; never copy placeholder wording.

## Frontmatter

Store list-valued fields as inline JSON arrays so the audit tool can verify them:

```yaml
---
title: "<中文主标题：副标题>"
topic: "<研究主题>"
search_keyword: "<用户原始关键词>"
query_variants: ["<variant-1>", "<variant-2>"]
research_id: "<manifest research_id>"
source_count: 5
source_video_ids: ["id-1", "id-2", "id-3", "id-4", "id-5"]
source_channels: ["channel-1", "channel-2", "channel-3", "channel-4", "channel-5"]
source_urls: ["https://www.youtube.com/watch?v=id-1", "..."]
source_transcripts: ["[[transcript-1]]", "[[transcript-2]]", "[[transcript-3]]", "[[transcript-4]]", "[[transcript-5]]"]
analysis_status: "complete"
analysis_method: "多源通读、第一性原理、交叉验证、因果推演、观点裁剪"
created: "<YYYY-MM-DD>"
tags:
  - topic-research
  - youtube-analysis
  - cross-validation
  - first-principles
---
```

Filename:

```text
<YYYY-MM-DD> - <concise-Chinese-title> [topic-<research-id>] - 深度解读.md
```

## Article skeleton

```markdown
# <能够表达最终判断的标题>

> [!abstract] 全文结论
> <问题、跨来源结论、主要分歧、底层机制与最终判断。>

## 研究概览：<多份材料共同指向什么问题>

<自然说明主题、资料范围和为什么这些来源能够形成互补视角。>

### 来源组合与研究范围

| 来源 | 角色与视角 | 主要贡献 | 需要保留的限制 |
|---|---|---|---|
| <频道/嘉宾> | <研究者/实践者/评论者> | <机制或证据> | <激励、范围或证据限制> |

### 这个主题真正要回答什么

<用 3–5 个编号问题组织全局理解。>

### 四个核心判断

<恰好四条完整判断。>

### 全文逻辑主线

```text
问题起点
→ 底层约束
→ 多源共识
→ 关键分歧
→ 更深机制
→ 可执行判断
```

<解释贯穿全文的主要张力。>

## <结论式章节标题，不添加“支柱一”等数字前缀>

> **推演主线：** A → B → C → D → E。

### 哲学原点：<底层原理>

<解释原理及其适用性。>

> [!summary] 最小命题
> <一句独立成立的压缩命题。>

**从 A 开始。** <用一个或多个来源说明起点。>

<解释每次因果转折，并自然写出来源之间的一致、限定或分歧。>

**真正的转折在于……** <推进到底层结构。>

**因此……** <形成综合判断与实践落点。>

<共写 6–9 个非重叠支柱；章节围绕机制，不围绕视频。>

## 交叉验证后的证据结构

| 关键命题 | 支持与来源关系 | 分歧或限制 | 证据强度 |
|---|---|---|---|
| <命题> | <独立支持或共同原始来源> | <反例、范围、定义差异> | 强 / 中 / 弱 |

<表后用连贯段落解释最重要的共识、真实分歧和仍只能保留为假设的部分。>

## 去掉热度、标题包装与单一立场之后，真正留下什么

<裁掉播放量、营销、人物光环、时间预测和重复报道，保留可迁移结构。>

## 核心洞察：<跨支柱、跨来源的新判断>

### 洞察一：<新判断>

<至少结合两个支柱和两个独立来源，写出二阶推导。>

<共 5–8 条。>

## 面向实践者的行动框架

### 1. <动作标题>

<动作、原因、完成或验证标准。>

<共 6–10 个有顺序的动作。>

## 最终判断：<一句有区分度的结论>

<收束共识、分歧、底层机制与真正值得下注的方向。>
```

## Layout rules

- Keep source transparency compact; do not turn the article into one summary per video.
- Use tables only for exact source mapping and the evidence matrix.
- Make causal viewpoint chapters the dominant share of the article.
- Write viewpoint H2 headings as article conclusions. Do not prefix them with `支柱一`、`核心观点二` or other numbered scaffolding.
- Use attribution where it changes confidence or scope; do not attach a source name to every sentence.
- Keep programme timestamps, search rankings, collection logs, and analysis-process narration out of the article.
- Apply `ai-terminology.md` consistently. In AI contexts write `Agent`、`Agentic`、`Coding Agent` and `多 Agent`, never “代理式”“编码代理” or “多代理”.
