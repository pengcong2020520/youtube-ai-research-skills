#!/usr/bin/env python3
"""Audit a Chinese podcast deep reading against the skill's structural contract."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


FM_BLOCK_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FM_FIELD_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
REQUIRED_FRONTMATTER = (
    "title",
    "creator",
    "source_title",
    "source_video_id",
    "source_url",
    "source_transcript",
    "analysis_status",
    "analysis_method",
    "created",
)
FORBIDDEN = {
    "analysis-step heading": re.compile(
        r"^#{1,6}\s+.*(?:第一步|第二步|第三步|通读全文|第一性原理提取)", re.MULTILINE
    ),
    "reduction scaffold": re.compile(r"把问题还原到不可简化的层次"),
    "anchor scaffold": re.compile(r"节目锚点|支点观点"),
    "audit-chain scaffold": re.compile(r"可审计(?:的)?(?:论证|逻辑)链"),
    "counterexample appendix": re.compile(r"^#{1,6}\s+.*边界与反证", re.MULTILINE),
    "unanswered appendix": re.compile(r"^#{1,6}\s+.*没有充分回答的问题", re.MULTILINE),
    "programme timetable": re.compile(r"^#{1,6}\s+.*(?:节目时间结构|时间结构)", re.MULTILINE),
    "missing-speaker meta": re.compile(r"逐字稿.{0,20}(?:没有|未).{0,12}标注.{0,20}(?:名字|主持人)"),
    "context-limit meta": re.compile(r"由于上下文(?:的)?限制|受限于上下文"),
}
TERMINOLOGY_ERRORS = {
    "AI Agent translated as proxy": re.compile(
        r"(?:AI|人工智能)\s*代理(?!商|服务|协议|权|机构)"
    ),
    "Agentic translated as proxy-style": re.compile(
        r"代理式(?:AI|软件|工程|编程|编码|开发|工作流|系统|生产|架构)"
    ),
    "Agent compound mistranslation": re.compile(
        r"(?:编码|代码|自主|智能|多|子|执行|实施|评审|协调|虚拟)\s*代理"
    ),
    "Agent concept mistranslation": re.compile(
        r"代理(?:会话|变更|运行(?:时|小时|量)?|数量|自评|管理|工作流|工具栈|"
        r"系统|时代|自主|失配|接管|生成|能力|循环|框架|管线|记忆|壳)"
    ),
}


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FM_BLOCK_RE.search(text)
    if not match:
        return {}
    return {
        key: value.strip().strip('"\'')
        for key, value in FM_FIELD_RE.findall(match.group(1))
    }


def section(text: str, start_pattern: str, end_pattern: str | None = None) -> str:
    start = re.search(start_pattern, text, re.MULTILINE)
    if not start:
        return ""
    body_start = start.end()
    if end_pattern:
        end = re.search(end_pattern, text[body_start:], re.MULTILINE)
        if end:
            return text[body_start : body_start + end.start()]
    return text[body_start:]


def measure(text: str) -> dict[str, Any]:
    body = FM_BLOCK_RE.sub("", text, count=1)
    pipelines = re.findall(r"^> \*\*推演主线：\*\*\s*(.+)$", body, re.MULTILINE)
    h2_matches = list(re.finditer(r"^##\s+.+$", body, re.MULTILINE))
    pillar_characters: list[int] = []
    for index, match in enumerate(h2_matches):
        end = h2_matches[index + 1].start() if index + 1 < len(h2_matches) else len(body)
        chunk = body[match.start() : end]
        if "> **推演主线：**" in chunk:
            pillar_characters.append(len(chunk))
    overview = section(
        body,
        r"^###\s+(?:这期节目|这篇文章|这篇内容)主要讨论什么\s*$",
        r"^###\s+",
    )
    judgments = section(body, r"^###\s+四个核心判断\s*$", r"^###\s+")
    insights = section(body, r"^##\s+核心洞察(?:：.*)?$", r"^##\s+面向实践者的行动框架")
    actions = section(body, r"^##\s+面向实践者的行动框架\s*$", r"^##\s+最终判断")
    global_spine = section(body, r"^###\s+全文逻辑主线\s*$", r"^##\s+")
    nonempty = [line for line in body.splitlines() if line.strip()]
    bullets = [line for line in nonempty if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line)]
    return {
        "characters": len(text),
        "body_characters": len(body),
        "paragraphs": len([part for part in re.split(r"\n\s*\n", body) if part.strip()]),
        "pipeline_count": len(pipelines),
        "pipeline_arrow_counts": [line.count("→") for line in pipelines],
        "pillar_character_counts": pillar_characters,
        "minimum_pillar_characters": min(pillar_characters) if pillar_characters else 0,
        "average_pillar_characters": round(
            sum(pillar_characters) / max(len(pillar_characters), 1), 1
        ),
        "global_spine_arrow_count": global_spine.count("→"),
        "philosophy_count": len(re.findall(r"^###\s+哲学原点(?:：.*)?$", body, re.MULTILINE)),
        "minimum_proposition_count": len(
            re.findall(r"^> \[!summary\]\s+最小命题\s*$", body, re.MULTILINE)
        ),
        "overview_question_count": len(re.findall(r"^\d+\.\s+", overview, re.MULTILINE)),
        "judgment_count": len(re.findall(r"^-\s+", judgments, re.MULTILINE)),
        "insight_count": len(re.findall(r"^###\s+洞察[^\n：:]*[：:]", insights, re.MULTILINE)),
        "action_count": len(re.findall(r"^###\s+\d+[\.、]\s+", actions, re.MULTILINE)),
        "bullet_line_ratio": round(len(bullets) / max(len(nonempty), 1), 4),
        "timecode_count": len(re.findall(r"(?<!\d)\d{1,2}:\d{2}(?::\d{2})?(?!\d)", body)),
        "terminology_violation_count": sum(
            len(pattern.findall(body)) for pattern in TERMINOLOGY_ERRORS.values()
        ),
    }


def load_references(directory: Path, current: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in directory.rglob("*深度解读.md"):
        if path.resolve() == current.resolve():
            continue
        try:
            results.append(measure(path.read_text(encoding="utf-8")))
        except OSError:
            continue
    return results


def median_reference(references: list[dict[str, Any]]) -> dict[str, float]:
    fields = (
        "body_characters",
        "pipeline_count",
        "insight_count",
        "action_count",
        "bullet_line_ratio",
    )
    return {
        field: round(statistics.median(float(item[field]) for item in references), 2)
        for field in fields
    }


def audit(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.analysis).expanduser().resolve()
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    metrics = measure(text)
    errors: list[str] = []
    warnings: list[str] = []

    if not frontmatter:
        errors.append("missing YAML frontmatter")
    for field in REQUIRED_FRONTMATTER:
        if not frontmatter.get(field):
            errors.append(f"missing frontmatter field: {field}")
    if frontmatter.get("analysis_status") not in {"complete", "sample-for-review"}:
        errors.append('analysis_status must be "complete"')
    video_id = frontmatter.get("source_video_id", "")
    if video_id and video_id not in frontmatter.get("source_url", ""):
        errors.append("source_url does not contain source_video_id")
    if video_id and video_id not in path.name:
        errors.append("filename does not contain source_video_id")

    required_patterns = {
        "abstract": r"^> \[!abstract\]\s+全文结论\s*$",
        "overview": r"^##\s+.*概览(?:：.*)?$",
        "overview questions": r"^###\s+(?:这期节目|这篇文章|这篇内容)主要讨论什么\s*$",
        "four judgments": r"^###\s+四个核心判断\s*$",
        "global causal spine": r"^###\s+全文逻辑主线\s*$",
        "viewpoint crop": r"^##\s+去掉.*真正留下什么\s*$",
        "core insights": r"^##\s+核心洞察(?:：.*)?$",
        "action framework": r"^##\s+面向实践者的行动框架\s*$",
        "final judgment": r"^##\s+最终判断(?:：.*)?$",
    }
    for label, pattern in required_patterns.items():
        if not re.search(pattern, text, re.MULTILINE):
            errors.append(f"missing required section: {label}")

    for label, pattern in FORBIDDEN.items():
        if pattern.search(text):
            errors.append(f"forbidden process language: {label}")
    for label, pattern in TERMINOLOGY_ERRORS.items():
        matches = pattern.findall(text)
        if matches:
            errors.append(f"forbidden AI terminology: {label} ({len(matches)} occurrence(s))")

    pillars = metrics["pipeline_count"]
    if not 6 <= pillars <= 9:
        errors.append(f"expected 6–9 viewpoint pillars, found {pillars}")
    if metrics["philosophy_count"] != pillars:
        errors.append(
            f"philosophy origins ({metrics['philosophy_count']}) do not match pillars ({pillars})"
        )
    if metrics["minimum_proposition_count"] != pillars:
        errors.append(
            "minimum propositions "
            f"({metrics['minimum_proposition_count']}) do not match pillars ({pillars})"
        )
    weak_lines = [count for count in metrics["pipeline_arrow_counts"] if count < 3]
    if weak_lines:
        errors.append(f"{len(weak_lines)} inference lines contain fewer than three causal arrows")
    if metrics["global_spine_arrow_count"] < 5:
        errors.append(
            "global causal spine contains fewer than five arrows; the overview may be too compressed"
        )
    if metrics["minimum_pillar_characters"] < 700:
        errors.append(
            "at least one viewpoint chapter is under 700 characters; explain the causal transitions"
        )
    if not 3 <= metrics["overview_question_count"] <= 5:
        errors.append(
            f"expected 3–5 overview questions, found {metrics['overview_question_count']}"
        )
    if metrics["judgment_count"] != 4:
        errors.append(f"expected exactly four core judgments, found {metrics['judgment_count']}")
    if not 5 <= metrics["insight_count"] <= 8:
        errors.append(f"expected 5–8 core insights, found {metrics['insight_count']}")
    if not 6 <= metrics["action_count"] <= 10:
        errors.append(f"expected 6–10 actions, found {metrics['action_count']}")
    if metrics["body_characters"] < 8000:
        errors.append(
            f"body is too compressed for a long-form deep reading ({metrics['body_characters']} characters)"
        )
    elif metrics["body_characters"] < 11000:
        warnings.append(
            f"body is below the accepted long-form calibration band ({metrics['body_characters']} characters)"
        )
    if metrics["bullet_line_ratio"] > 0.18:
        warnings.append(
            f"bullet density is high ({metrics['bullet_line_ratio']:.1%}); check for fragmented prose"
        )
    if metrics["timecode_count"]:
        errors.append(f"found {metrics['timecode_count']} programme-style timecodes")

    transcript_result: dict[str, Any] | None = None
    if args.transcript:
        transcript_path = Path(args.transcript).expanduser().resolve()
        transcript_text = transcript_path.read_text(encoding="utf-8")
        transcript_fm = parse_frontmatter(transcript_text)
        transcript_id = transcript_fm.get("youtube_video_id", "")
        transcript_result = {
            "path": str(transcript_path),
            "characters": len(transcript_text),
            "youtube_video_id": transcript_id,
        }
        if not transcript_id:
            errors.append("transcript is missing youtube_video_id")
        elif transcript_id != video_id:
            errors.append(
                f"analysis video ID {video_id!r} does not match transcript ID {transcript_id!r}"
            )
        expected_link = transcript_path.stem
        if expected_link not in frontmatter.get("source_transcript", ""):
            errors.append("source_transcript does not link the audited transcript filename")

    references: list[dict[str, Any]] = []
    reference_summary: dict[str, Any] | None = None
    if args.reference_dir:
        references = load_references(Path(args.reference_dir).expanduser().resolve(), path)
        if references:
            medians = median_reference(references)
            reference_summary = {"count": len(references), "median": medians}
            ratio = metrics["body_characters"] / max(medians["body_characters"], 1)
            reference_summary["body_character_ratio"] = round(ratio, 3)
            if ratio < 0.72:
                warnings.append(
                    f"body is only {ratio:.0%} of the reference median; inspect for lost depth"
                )
            elif ratio > 1.55:
                warnings.append(
                    f"body is {ratio:.0%} of the reference median; inspect for repetition or padding"
                )
        else:
            warnings.append("reference directory contains no comparable deep readings")

    score = max(0, 100 - 10 * len(errors) - 2 * len(warnings))
    return {
        "analysis": str(path),
        "status": "pass" if not errors and score >= 80 else "fail",
        "score": score,
        "frontmatter": frontmatter,
        "metrics": metrics,
        "transcript": transcript_result,
        "reference_comparison": reference_summary,
        "errors": errors,
        "warnings": warnings,
        "manual_review_required": [
            "complete-transcript coverage",
            "causal validity of every transition",
            "non-overlapping and collectively sufficient pillars",
            "newly derived cross-pillar insights",
            "practical and verifiable action sequence",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", help="Deep-reading Markdown file")
    parser.add_argument("--transcript", help="Source transcript Markdown file")
    parser.add_argument("--reference-dir", help="Directory containing accepted analyses")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = audit(args)
    except (OSError, UnicodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status'].upper()} score={result['score']} {result['analysis']}")
        for key, value in result["metrics"].items():
            print(f"  {key}: {value}")
        if result["reference_comparison"]:
            print(
                "  reference median: "
                + json.dumps(result["reference_comparison"], ensure_ascii=False)
            )
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
        print("Manual review remains required for semantic quality.")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
