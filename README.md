# YouTube AI Research Skills

两个面向 Codex / Agent Skills 的 YouTube 研究工作流：

- `youtube-podcast-deep-analysis`：按博主增量采集公开逐字稿，并逐篇生成中文第一性原理深度解读。
- `youtube-topic-research-analysis`：按关键词搜索多个独立频道，采集逐字稿、交叉验证观点，并生成中文主题研究报告。

两者都只处理公开元数据与字幕，不下载视频或音频。

## 能力概览

| Skill | 输入 | 输出 | 去重方式 |
|---|---|---|---|
| Podcast Deep Analysis | 博主名、Handle、频道 URL 或内置 AI 播客集合 | `逐字稿/<博主>/` 与 `分析/<博主>/` | YouTube video ID |
| Topic Research Analysis | 主题或关键词 | 多源逐字稿、研究 manifest 与 `分析/主题研究/` 报告 | YouTube video ID + source set |

两套工作流均内置：

- Obsidian 兼容 Markdown；
- 增量采集与重复检测；
- 全文阅读约束；
- 第一性原理推导模板；
- AI 专业术语表；
- 确定性质量审计脚本；
- 对来源独立性、反方观点和证据边界的检查。

## 安装

使用 `npx skills`：

```bash
npx skills add https://github.com/pengcong2020520/youtube-ai-research-skills \
  --skill youtube-podcast-deep-analysis

npx skills add https://github.com/pengcong2020520/youtube-ai-research-skills \
  --skill youtube-topic-research-analysis
```

也可以手动复制：

```bash
git clone https://github.com/pengcong2020520/youtube-ai-research-skills.git
cp -R youtube-ai-research-skills/skills/youtube-podcast-deep-analysis ~/.codex/skills/
cp -R youtube-ai-research-skills/skills/youtube-topic-research-analysis ~/.codex/skills/
```

## 运行要求

- Python 3
- Node.js 与 npm
- 可访问 YouTube 的网络环境
- 目标内容仓库或 Obsidian vault

首次抓取需要在用户明确同意后，为私有缓存安装 `yt-dlp` 与 `defuddle`。Skill 默认不会自行安装，也不会写入全局 Python 或 npm 环境。

按博主模式首次授权：

```bash
YTPDA_ALLOW_INSTALL=1 bash \
  ~/.codex/skills/youtube-podcast-deep-analysis/scripts/fetch.sh \
  "@channel" --limit 10 --output-root "/path/to/content-repository"
```

主题研究模式首次授权：

```bash
YTTOPIC_ALLOW_INSTALL=1 bash \
  ~/.codex/skills/youtube-topic-research-analysis/scripts/run.sh \
  "your keyword" --dry-run --output-root "/path/to/content-repository"
```

依赖安装在：

```text
${XDG_CACHE_HOME:-$HOME/.cache}/youtube-transcripts-to-obsidian
```

后续运行不需要再次设置 `*_ALLOW_INSTALL=1`。如果 YouTube 或依赖发生变化，可以清理该私有缓存后重新授权安装。

## 使用示例

在 Codex 中：

```text
使用 youtube-podcast-deep-analysis，获取 @lexfridman 最新 10 期公开逐字稿，
只分析尚未生成深度解读的节目。
```

```text
使用 youtube-topic-research-analysis，研究 “Graph Engineering”，
选择至少 3 个独立频道进行交叉验证，并生成中文深度报告。
```

两个 Skill 都支持：

1. 完整流程；
2. 仅采集逐字稿或主题语料；
3. 只分析已经存在的逐字稿或 manifest。

## 输出目录

```text
内容仓库/
├── 逐字稿/
│   ├── <博主>/
│   └── 主题研究/<关键词>/
└── 分析/
    ├── <博主>/
    └── 主题研究/<关键词>/
```

主题研究同时生成版本化的 `research-manifest-<id>.json`，保存来源选择、复用记录和研究 ID。

## 重要限制

- 只读取公开视频的可访问字幕；没有字幕或字幕接口不可访问时，不会自动下载音频做转写。
- “多个频道”不等于“独立证据”。主题 Skill 会继续检查是否共同引用了同一篇论文、新闻稿或公司声明。
- 热度排序只是候选筛选信号，不代表内容真实。
- 自动审计通过不替代人工语义检查。
- 请遵守 YouTube 服务条款、版权规则及所在地法律，只保存和使用你有权处理的内容。

## 仓库结构

```text
skills/
├── youtube-podcast-deep-analysis/
│   ├── SKILL.md
│   ├── agents/
│   ├── references/
│   └── scripts/
└── youtube-topic-research-analysis/
    ├── SKILL.md
    ├── agents/
    ├── references/
    └── scripts/
```

## License

[MIT](LICENSE)
