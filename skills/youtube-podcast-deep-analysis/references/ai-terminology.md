# AI 中英术语规范

Use this glossary whenever English AI material is rewritten into Chinese. Preserve the field's professional vocabulary before optimising for surface fluency.

## Agent word family

| English source term | Required output | Do not write |
|---|---|---|
| agent / AI agent | `Agent` / `AI Agent` | 代理、AI 代理、智能代理 |
| agentic | `Agentic` | 代理式、智能体式 |
| agentic coding | `Agentic Coding` | 代理式编码 |
| agentic engineering | `Agentic Engineering` or `Agentic 工程` | 代理式工程 |
| agentic workflow | `Agentic 工作流` | 代理工作流、代理式工作流 |
| coding agent | `Coding Agent` | 编码代理、代码代理 |
| multi-agent | `多 Agent` | 多代理 |
| subagent | `子 Agent` | 子代理 |
| agent-to-agent | `Agent-to-Agent` | 代理到代理 |
| agent harness | first use `Agent harness（运行与工具编排层）`, then `Agent harness` | 代理壳、代理框架 |
| agent loop | `Agent loop（Agent 循环）` | 代理循环 |
| agent runtime | `Agent runtime（运行时）` | 代理运行时 |
| agent memory | `Agent memory` or `Agent 记忆` | 代理记忆 |

`Agent` is capitalised in Chinese prose and separated from adjacent Chinese characters by a space where needed: `多 Agent 系统`、`Agent 工作流`、`让 Agent 执行`.

## Important disambiguation

Do not mechanically replace every English `agent`:

- `agency` describing a person or organisation → `能动性`、`主动性` or `行动自主性`, according to context.
- `principal–agent problem` → `委托—代理问题`.
- sales agent / channel agent → `代理商` or `渠道代理`.
- proxy / reverse proxy → `代理` / `反向代理`.
- literary, legal, diplomatic, or biological agent → translate by that domain's meaning.

When the source discusses an AI system that plans, uses tools, keeps state, or acts toward a goal, retain `Agent`.

## Other high-signal AI terms

| English source term | Preferred output |
|---|---|
| prompt | `prompt` or `提示词`; choose once and stay consistent |
| system prompt | `system prompt（系统提示词）` on first use |
| context window | `上下文窗口` |
| context engineering | `Context Engineering（上下文工程）` on first use |
| token | `token` |
| embedding | `embedding（向量嵌入）` on first use |
| weights / parameters | `权重` / `参数` |
| pre-training / mid-training / post-training | `预训练` / `中期训练` / `后训练` |
| fine-tuning | `微调` |
| reinforcement learning | `强化学习` |
| RLVR | first use `可验证奖励强化学习（RLVR）`, then `RLVR` |
| inference | `推理` |
| inference-time compute | `推理时计算` |
| reasoning | `推理` or `推理能力`, not generic “思考” when technical |
| rollout | `rollout（采样轨迹）` on first use, then `rollout` |
| eval / evaluation | `eval（评测）` on first use, then stay consistent |
| benchmark | `benchmark（基准测试）` on first use |
| world model | `世界模型` |
| alignment | `对齐` |
| hallucination | `幻觉` |
| RAG | first use `检索增强生成（RAG）`, then `RAG` |
| mixture of experts | `Mixture of Experts（MoE）` on first use |
| scaling law | `Scaling Law（规模定律）` on first use |
| open weights | `开放权重` |
| open source | `开源`; never collapse it with `开放权重` |
| latency / throughput | `时延` / `吞吐量` |
| test-time compute | `测试时计算` |
| chain of thought | `思维链（Chain of Thought）` when the term itself matters |
| harness | retain `harness`, with a precise Chinese gloss on first use |

## Translation workflow

1. Build a private source-term map before drafting.
2. Preserve product names, model names, acronyms, paper terms, and field-standard English.
3. On first occurrence, use `English term（precise Chinese gloss）` only when a gloss helps; later keep one stable form.
4. Never alternate among `Agent`、`代理`、`智能体` for stylistic variety.
5. If no Chinese term preserves the technical scope, retain the English and explain it once.
6. Quote a source's unusual translation only when the wording itself matters, and immediately normalise the article's own terminology.
7. Run the terminology audit after the language-cleaning pass.
