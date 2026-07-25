#!/usr/bin/env python3
"""List transcript notes that do not yet have a deep analysis."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELD_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_-]*):\s*["\']?(.*?)["\']?\s*$', re.MULTILINE)
ID_IN_NAME_RE = re.compile(r"\[([A-Za-z0-9_-]{6,20})\]")


def frontmatter(path: Path) -> dict[str, str]:
    try:
        head = path.read_text(encoding="utf-8")[:20000]
    except OSError:
        return {}
    match = FM_RE.search(head)
    if not match:
        return {}
    return {key: value.strip().strip('"\'') for key, value in FIELD_RE.findall(match.group(1))}


def video_id(path: Path, data: dict[str, str], field: str) -> str:
    value = data.get(field, "")
    if value:
        return value
    match = ID_IN_NAME_RE.search(path.name)
    return match.group(1) if match else ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Content repository root")
    parser.add_argument("--creator", help="Exact creator folder to inspect")
    parser.add_argument("--limit", type=int, default=10, help="Maximum pending notes to return")
    args = parser.parse_args()
    if not 1 <= args.limit <= 1000:
        parser.error("--limit must be between 1 and 1000")
    return args


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).expanduser().resolve()
    transcript_root = root / "逐字稿"
    analysis_root = root / "分析"
    if not transcript_root.is_dir():
        raise SystemExit(f"Transcript directory not found: {transcript_root}")

    analysis_ids: set[str] = set()
    if analysis_root.is_dir():
        for path in analysis_root.rglob("*.md"):
            data = frontmatter(path)
            identifier = video_id(path, data, "source_video_id")
            if identifier:
                analysis_ids.add(identifier)

    scan_root = transcript_root / args.creator if args.creator else transcript_root
    paths = sorted(scan_root.rglob("*.md")) if scan_root.is_dir() else []
    records: list[dict[str, str]] = []
    for path in paths:
        data = frontmatter(path)
        identifier = video_id(path, data, "youtube_video_id")
        if not identifier:
            continue
        creator = data.get("creator") or path.parent.name
        records.append(
            {
                "video_id": identifier,
                "creator": creator,
                "published": data.get("published", ""),
                "title": data.get("title") or path.stem,
                "source": data.get("source", ""),
                "path": str(path.resolve()),
                "status": "analysed" if identifier in analysis_ids else "pending",
            }
        )

    records.sort(key=lambda item: (item["published"] or "0000-00-00", item["path"]), reverse=True)
    pending = [item for item in records if item["status"] == "pending"]
    return {
        "root": str(root),
        "creator": args.creator,
        "transcript_count": len(records),
        "analysed_count": len(records) - len(pending),
        "pending_count": len(pending),
        "pending": pending[: args.limit],
    }


if __name__ == "__main__":
    print(json.dumps(run(parse_args()), ensure_ascii=False, indent=2))
