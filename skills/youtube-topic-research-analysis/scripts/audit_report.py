#!/usr/bin/env python3
"""Audit a multi-source YouTube topic research report."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


FM_BLOCK_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FM_FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", re.MULTILINE)
REQUIRED_FRONTMATTER = (
    "title",
    "topic",
    "search_keyword",
    "query_variants",
    "research_id",
    "source_count",
    "source_video_ids",
    "source_channels",
    "source_urls",
    "source_transcripts",
    "analysis_status",
    "analysis_method",
    "created",
)
ARRAY_FIELDS = (
    "query_variants",
    "source_video_ids",
    "source_channels",
    "source_urls",
    "source_transcripts",
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
    "numbered pillar heading": re.compile(
        r"^##\s+(?:支柱|核心观点)[一二三四五六七八九十\d]+[：:、.]?", re.MULTILINE
    ),
    "context-limit meta": re.compile(r"由于上下文(?:的)?限制|受限于上下文"),
    "vote-count fallacy": re.compile(r"这些视频都提到了.{0,12}(?:所以|因此).{0,8}(?:证明|证实)"),
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
    result: dict[str, str] = {}
    for key, raw in FM_FIELD_RE.findall(match.group(1)):
        value = raw.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                result[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        result[key] = value.strip("\"'")
    return result


def parse_array(frontmatter: dict[str, str], field: str, errors: list[str]) -> list[str]:
    raw = frontmatter.get(field, "")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        errors.append(f"{field} must be an inline JSON array")
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{field} must contain only strings")
        return []
    return value


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


def table_data_rows(value: str) -> int:
    rows = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        if re.fullmatch(r"\|?[\s:|\-]+\|?", stripped):
            continue
        rows.append(stripped)
    return max(len(rows) - 1, 0)


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
        r"^###\s+这个主题真正要回答什么\s*$",
        r"^###\s+",
    )
    judgments = section(body, r"^###\s+四个核心判断\s*$", r"^###\s+")
    source_scope = section(body, r"^###\s+来源组合与研究范围\s*$", r"^###\s+")
    global_spine = section(body, r"^###\s+全文逻辑主线\s*$", r"^##\s+")
    evidence = section(body, r"^##\s+交叉验证后的证据结构\s*$", r"^##\s+")
    insights = section(body, r"^##\s+核心洞察(?:：.*)?$", r"^##\s+面向实践者的行动框架")
    actions = section(body, r"^##\s+面向实践者的行动框架\s*$", r"^##\s+最终判断")
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
        "philosophy_count": len(
            re.findall(r"^###\s+哲学原点(?:：.*)?$", body, re.MULTILINE)
        ),
        "minimum_proposition_count": len(
            re.findall(r"^> \[!summary\]\s+最小命题\s*$", body, re.MULTILINE)
        ),
        "overview_question_count": len(re.findall(r"^\d+\.\s+", overview, re.MULTILINE)),
        "judgment_count": len(re.findall(r"^-\s+", judgments, re.MULTILINE)),
        "source_table_rows": table_data_rows(source_scope),
        "evidence_table_rows": table_data_rows(evidence),
        "cross_validation_term_count": len(
            re.findall(
                r"独立(?:支持|来源|验证)|共享(?:来源|原始)|共同(?:来源|原始)|"
                r"分歧|证据强度|单一来源|范围差异|定义差异",
                evidence,
            )
        ),
        "insight_count": len(
            re.findall(r"^###\s+洞察[^\n：:]*[：:]", insights, re.MULTILINE)
        ),
        "action_count": len(re.findall(r"^###\s+\d+[\.、]\s+", actions, re.MULTILINE)),
        "bullet_line_ratio": round(len(bullets) / max(len(nonempty), 1), 4),
        "timecode_count": len(
            re.findall(r"(?<!\d)\d{1,2}:\d{2}(?::\d{2})?(?!\d)", body)
        ),
        "terminology_violation_count": sum(
            len(pattern.findall(body)) for pattern in TERMINOLOGY_ERRORS.values()
        ),
    }


def reference_summary(directory: Path, current: Path) -> dict[str, Any] | None:
    values = []
    if not directory.is_dir():
        return None
    for path in directory.rglob("*深度解读.md"):
        if path.resolve() == current.resolve():
            continue
        try:
            values.append(measure(path.read_text(encoding="utf-8"))["body_characters"])
        except OSError:
            continue
    if not values:
        return None
    return {
        "count": len(values),
        "body_characters_min": min(values),
        "body_characters_median": round(statistics.median(values), 1),
        "body_characters_max": max(values),
    }


def audit(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.report).expanduser().resolve()
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
    arrays = {field: parse_array(frontmatter, field, errors) for field in ARRAY_FIELDS}
    try:
        source_count = int(frontmatter.get("source_count", "0"))
    except ValueError:
        source_count = 0
        errors.append("source_count must be an integer")

    if frontmatter.get("analysis_status") != "complete":
        errors.append('analysis_status must be "complete"')
    research_id = frontmatter.get("research_id", "")
    if research_id and f"topic-{research_id}" not in path.name:
        errors.append("filename does not contain topic research_id")
    if source_count < 3:
        errors.append(f"at least three sources are required, found {source_count}")
    for field in ("source_video_ids", "source_channels", "source_urls", "source_transcripts"):
        if len(arrays[field]) != source_count:
            errors.append(f"{field} count does not match source_count")
    if len(set(arrays["source_video_ids"])) != len(arrays["source_video_ids"]):
        errors.append("source_video_ids contains duplicates")
    if len(set(arrays["source_channels"])) < 3:
        errors.append("fewer than three unique source channels")
    for video_id, url in zip(arrays["source_video_ids"], arrays["source_urls"]):
        if video_id not in url:
            errors.append(f"source URL does not contain video ID {video_id}")

    required_patterns = {
        "abstract": r"^> \[!abstract\]\s+全文结论\s*$",
        "research overview": r"^##\s+研究概览(?:：.*)?$",
        "source scope": r"^###\s+来源组合与研究范围\s*$",
        "research questions": r"^###\s+这个主题真正要回答什么\s*$",
        "four judgments": r"^###\s+四个核心判断\s*$",
        "global causal spine": r"^###\s+全文逻辑主线\s*$",
        "cross-validation evidence": r"^##\s+交叉验证后的证据结构\s*$",
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
        errors.append(f"{len(weak_lines)} inference lines contain fewer than three arrows")
    if metrics["minimum_pillar_characters"] < 750:
        errors.append("at least one viewpoint chapter is under 750 characters")
    if metrics["global_spine_arrow_count"] < 5:
        errors.append("global causal spine contains fewer than five arrows")
    if not 3 <= metrics["overview_question_count"] <= 5:
        errors.append(
            f"expected 3–5 research questions, found {metrics['overview_question_count']}"
        )
    if metrics["judgment_count"] != 4:
        errors.append(f"expected four core judgments, found {metrics['judgment_count']}")
    if metrics["source_table_rows"] < source_count:
        errors.append(
            f"source table has {metrics['source_table_rows']} rows for {source_count} sources"
        )
    if metrics["evidence_table_rows"] < 5:
        errors.append(
            f"cross-validation table needs at least five claims, found {metrics['evidence_table_rows']}"
        )
    if metrics["cross_validation_term_count"] < 3:
        warnings.append("evidence section may not distinguish source independence and disagreement")
    if not 5 <= metrics["insight_count"] <= 8:
        errors.append(f"expected 5–8 core insights, found {metrics['insight_count']}")
    if not 6 <= metrics["action_count"] <= 10:
        errors.append(f"expected 6–10 actions, found {metrics['action_count']}")
    if metrics["body_characters"] < 10000:
        errors.append(
            f"body is too compressed for multi-source synthesis ({metrics['body_characters']})"
        )
    elif metrics["body_characters"] < 13000:
        warnings.append(
            f"body is below the usual multi-source depth band ({metrics['body_characters']})"
        )
    if metrics["bullet_line_ratio"] > 0.20:
        warnings.append(
            f"bullet density is high ({metrics['bullet_line_ratio']:.1%}); inspect fragmentation"
        )
    if metrics["timecode_count"]:
        errors.append(f"found {metrics['timecode_count']} programme-style timecodes")

    manifest_result: dict[str, Any] | None = None
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        selected = manifest.get("selected") or []
        manifest_ids = [str(item.get("id") or "") for item in selected]
        manifest_channels = [str(item.get("channel") or "") for item in selected]
        manifest_result = {
            "path": str(manifest_path),
            "research_id": manifest.get("research_id"),
            "keyword": manifest.get("keyword"),
            "quality_gate_met": manifest.get("quality_gate_met"),
            "selected_count": len(selected),
            "source_count": manifest.get("source_count"),
        }
        if not manifest.get("quality_gate_met"):
            errors.append("manifest source-quality gate did not pass")
        if manifest.get("research_id") != research_id:
            errors.append("report research_id does not match manifest")
        if manifest.get("keyword") != frontmatter.get("search_keyword"):
            errors.append("report search_keyword does not match manifest")
        if set(manifest_ids) != set(arrays["source_video_ids"]):
            errors.append("report source_video_ids do not match manifest")
        if set(manifest_channels) != set(arrays["source_channels"]):
            errors.append("report source_channels do not match manifest")
        transcript_links = arrays["source_transcripts"]
        for item in selected:
            transcript_path = Path(str(item.get("path") or ""))
            if not transcript_path.name:
                errors.append(f"manifest source {item.get('id')} has no transcript path")
                continue
            if not any(transcript_path.stem in link for link in transcript_links):
                errors.append(f"source_transcripts does not link {transcript_path.name}")

    references = None
    if args.reference_dir:
        references = reference_summary(Path(args.reference_dir).expanduser().resolve(), path)
        if references:
            ratio = metrics["body_characters"] / max(
                float(references["body_characters_median"]), 1
            )
            references["body_character_ratio"] = round(ratio, 3)
            if ratio < 0.80:
                warnings.append(
                    f"body is only {ratio:.0%} of the reference median; inspect lost depth"
                )
            elif ratio > 1.80:
                warnings.append(
                    f"body is {ratio:.0%} of the reference median; inspect repetition"
                )
        else:
            warnings.append("reference directory contains no comparable reports")

    score = max(0, 100 - len(errors) * 10 - len(warnings) * 2)
    return {
        "report": str(path),
        "status": "pass" if not errors and score >= 80 else "fail",
        "score": score,
        "frontmatter": frontmatter,
        "metrics": metrics,
        "manifest": manifest_result,
        "reference_comparison": references,
        "errors": errors,
        "warnings": warnings,
        "manual_review_required": [
            "every selected transcript read to EOF",
            "independent support distinguished from shared-origin repetition",
            "genuine disagreement preserved",
            "causal validity and non-overlapping pillars",
            "new cross-source insights",
            "evidence table consistent with prose",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", help="Multi-source research Markdown")
    parser.add_argument("--manifest", help="Versioned research manifest JSON")
    parser.add_argument("--reference-dir", help="Accepted analysis directory")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = audit(args)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status'].upper()} score={result['score']} {result['report']}")
        for key, value in result["metrics"].items():
            print(f"  {key}: {value}")
        if result["manifest"]:
            print("  manifest: " + json.dumps(result["manifest"], ensure_ascii=False))
        if result["reference_comparison"]:
            print(
                "  reference: "
                + json.dumps(result["reference_comparison"], ensure_ascii=False)
            )
        for error in result["errors"]:
            print(f"ERROR: {error}")
        for warning in result["warnings"]:
            print(f"WARN: {warning}")
        print("Manual semantic review remains required.")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
