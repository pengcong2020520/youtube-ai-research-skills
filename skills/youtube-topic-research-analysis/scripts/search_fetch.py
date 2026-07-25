#!/usr/bin/env python3
"""Search YouTube, rank diverse long-form sources, and fetch transcript notes."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,20}$")
FRONTMATTER_ID_RE = re.compile(
    r"^youtube_video_id:\s*[\"']?([A-Za-z0-9_-]{6,20})[\"']?\s*$", re.MULTILINE
)
CLICKBAIT_RE = re.compile(
    r"\b(?:get rich|make money|no coding|become a pro|top \d+|everything you missed|"
    r"you(?:'|’)re not behind|endgame|insane|secret|shocking|full course|"
    r"for beginners|master \w+ in|complete tutorial)\b",
    re.IGNORECASE,
)
SUBSTANCE_RE = re.compile(
    r"\b(?:research|paper|benchmark|experiment|engineering|technical|interview|"
    r"evaluation|evidence|study|deployment|production|architecture)\b",
    re.IGNORECASE,
)


class UserFacingError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def query_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+|[\u3400-\u9fff]{2,}", normalize(value))


def safe_component(
    value: str, *, fallback: str, max_length: int = 90, max_bytes: int = 180
) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\x00-\x1f/\\:*?\"<>|]", "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .-") or fallback
    value = value[:max_length].rstrip(" .-")
    encoded = value.encode("utf-8")
    if len(encoded) > max_bytes:
        value = encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip(" .-")
    return value or fallback


def yaml_string(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def normalize_date(value: Any) -> str:
    if not value:
        return ""
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    if match:
        return match.group(0)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    return ""


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return default
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UserFacingError(f"Cannot read {path}: {exc}") from exc
    return value if isinstance(value, dict) else default


def cookie_tuple(value: str | None) -> tuple[str, ...] | None:
    if not value:
        return None
    browser, separator, profile = value.partition(":")
    return (browser, profile) if separator else (browser,)


def ydl_options(args: argparse.Namespace, **extra: Any) -> dict[str, Any]:
    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "skip_download": True,
    }
    cookies = cookie_tuple(args.cookies_from_browser)
    if cookies:
        options["cookiesfrombrowser"] = cookies
    options.update(extra)
    return options


def flat_search(query: str, limit: int, args: argparse.Namespace) -> list[dict[str, Any]]:
    from yt_dlp import YoutubeDL

    log(f"Searching YouTube: {query}")
    with YoutubeDL(
        ydl_options(args, extract_flat="in_playlist", playlistend=limit, lazy_playlist=False)
    ) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    results: list[dict[str, Any]] = []
    for rank, entry in enumerate((info or {}).get("entries") or [], start=1):
        if not isinstance(entry, dict):
            continue
        video_id = str(entry.get("id") or "")
        if not VIDEO_ID_RE.fullmatch(video_id):
            continue
        results.append(
            {
                "id": video_id,
                "title": str(entry.get("title") or video_id),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "channel": str(entry.get("channel") or entry.get("uploader") or ""),
                "channel_id": str(entry.get("channel_id") or entry.get("uploader_id") or ""),
                "duration": int(entry.get("duration") or 0),
                "view_count": int(entry.get("view_count") or 0),
                "query_hits": [query],
                "best_search_rank": rank,
            }
        )
    return results


def preliminary_score(item: dict[str, Any], queries: list[str]) -> float:
    title = normalize(item.get("title", ""))
    coverage = max(
        (
            sum(1 for token in query_tokens(query) if token in title)
            / max(len(query_tokens(query)), 1)
        )
        for query in queries
    )
    views = int(item.get("view_count") or 0)
    duration = int(item.get("duration") or 0)
    duration_bonus = 7 if 900 <= duration <= 7200 else 3 if duration >= 600 else -8
    return (
        coverage * 30
        + min(math.log10(views + 1) * 7, 48)
        + max(0, 10 - int(item.get("best_search_rank") or 50) * 0.35)
        + duration_bonus
    )


def enrich_one(item: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    from yt_dlp import YoutubeDL

    try:
        with YoutubeDL(ydl_options(args)) as ydl:
            info = ydl.extract_info(item["url"], download=False) or {}
    except Exception as exc:
        enriched = dict(item)
        enriched["metadata_error"] = str(exc)
        return enriched
    enriched = dict(item)
    for field in (
        "title",
        "description",
        "channel",
        "channel_id",
        "duration",
        "view_count",
        "like_count",
        "comment_count",
        "channel_follower_count",
        "upload_date",
        "timestamp",
    ):
        if info.get(field) is not None:
            enriched[field] = info[field]
    enriched["published"] = normalize_date(info.get("upload_date") or info.get("timestamp"))
    return enriched


def days_old(published: str) -> int | None:
    if not published:
        return None
    try:
        date = datetime.strptime(published, "%Y-%m-%d").date()
    except ValueError:
        return None
    return max((datetime.now().date() - date).days, 1)


def final_score(
    item: dict[str, Any], queries: list[str], recency_days: int
) -> tuple[float, list[str], float]:
    title = normalize(str(item.get("title") or ""))
    description = normalize(str(item.get("description") or ""))
    searchable = f"{title} {description}"
    coverages = []
    for query in queries:
        tokens = query_tokens(query)
        coverages.append(sum(1 for token in tokens if token in searchable) / max(len(tokens), 1))
    relevance = max(coverages or [0.0])
    views = int(item.get("view_count") or 0)
    likes = int(item.get("like_count") or 0)
    comments = int(item.get("comment_count") or 0)
    followers = int(item.get("channel_follower_count") or 0)
    duration = int(item.get("duration") or 0)
    age = days_old(str(item.get("published") or ""))

    view_score = min(math.log10(views + 1) * 7, 48)
    velocity_score = 0.0 if age is None else min(math.log10(views / age + 1) * 4, 20)
    recency_score = (
        4.0
        if age is None
        else max(0.0, 12.0 * (1 - age / max(recency_days, 1)))
        if recency_days
        else 4.0
    )
    engagement = min((likes / max(views, 1)) * 100, 8) + min(
        (comments / max(views, 1)) * 400, 4
    )
    authority = min(math.log10(followers + 1) * 2, 12)
    duration_score = (
        10 if 1200 <= duration <= 7200 else 7 if 600 <= duration <= 14400 else 2
    )
    substance = min(len(SUBSTANCE_RE.findall(searchable)) * 1.2, 6)
    clickbait = 11 if CLICKBAIT_RE.search(title) else 0
    rank_score = max(0, 8 - int(item.get("best_search_rank") or 50) * 0.25)
    score = (
        relevance * 30
        + view_score
        + velocity_score
        + recency_score
        + engagement
        + authority
        + duration_score
        + substance
        + rank_score
        - clickbait
    )
    reasons = [
        f"关键词覆盖 {relevance:.0%}",
        f"播放量 {views:,}",
        f"时长 {duration // 60} 分钟",
    ]
    if age is not None:
        reasons.append(f"发布 {age} 天")
    if velocity_score >= 12:
        reasons.append("近期传播速度较高")
    if substance >= 3:
        reasons.append("简介含研究或工程信号")
    if clickbait:
        reasons.append("标题存在营销信号，已降权")
    return round(score, 3), reasons, relevance


def merge_searches(searches: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for results in searches:
        for item in results:
            current = merged.get(item["id"])
            if current is None:
                merged[item["id"]] = dict(item)
                continue
            current["best_search_rank"] = min(
                int(current.get("best_search_rank") or 999),
                int(item.get("best_search_rank") or 999),
            )
            current["query_hits"] = sorted(
                set(current.get("query_hits") or []) | set(item.get("query_hits") or [])
            )
            if int(item.get("view_count") or 0) > int(current.get("view_count") or 0):
                for field in ("view_count", "duration", "title", "channel", "channel_id"):
                    current[field] = item.get(field)
    return list(merged.values())


def existing_transcripts(root: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    if not root.is_dir():
        return found
    for path in root.rglob("*.md"):
        try:
            head = path.read_text(encoding="utf-8")[:16000]
        except OSError:
            continue
        match = FRONTMATTER_ID_RE.search(head)
        if match and match.group(1) not in found:
            found[match.group(1)] = str(path.resolve())
    return found


def defuddle_extract(url: str, language: str, timeout: int) -> dict[str, Any]:
    executable = os.environ.get("DEFUDDLE_BIN") or "defuddle"
    try:
        process = subprocess.run(
            [executable, "parse", url, "--json", "--lang", language],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise UserFacingError("Defuddle is unavailable. Run through scripts/run.sh.") from exc
    except subprocess.TimeoutExpired as exc:
        raise UserFacingError(f"Defuddle timed out after {timeout}s") from exc
    if process.returncode != 0:
        detail = process.stderr.strip().splitlines()[-1] if process.stderr.strip() else "unknown"
        raise UserFacingError(f"Defuddle failed: {detail}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise UserFacingError("Defuddle returned invalid JSON.") from exc


def transcript_from_payload(payload: dict[str, Any]) -> str:
    transcript = str((payload.get("variables") or {}).get("transcript") or "").strip()
    if not transcript:
        raise UserFacingError("No accessible transcript/captions were returned.")
    return transcript


def render_note(
    item: dict[str, Any],
    *,
    keyword: str,
    title: str,
    channel: str,
    published: str,
    language: str,
    transcript: str,
) -> str:
    return "\n".join(
        [
            "---",
            f"title: {yaml_string(title)}",
            f"creator: {yaml_string(channel)}",
            f"research_keyword: {yaml_string(keyword)}",
            f"youtube_channel: {yaml_string(channel)}",
            f"youtube_video_id: {yaml_string(item['id'])}",
            f"source: {yaml_string(item['url'])}",
            f"published: {yaml_string(published)}",
            f"captured: {yaml_string(iso_now())}",
            f"transcript_language: {yaml_string(language)}",
            'transcript_source: "defuddle"',
            f"view_count_at_capture: {int(item.get('view_count') or 0)}",
            f"duration_seconds: {int(item.get('duration') or 0)}",
            "tags:",
            "  - youtube-transcript",
            "  - topic-research",
            "---",
            "",
            f"# {title}",
            "",
            "> [!info] 视频信息",
            f"> - 研究关键词：{keyword}",
            f"> - 频道：{channel}",
            f"> - 发布日期：{published or '未知'}",
            f"> - 采集时播放量：{int(item.get('view_count') or 0):,}",
            f"> - [在 YouTube 观看]({item['url']})",
            "",
            "## 逐字稿",
            "",
            transcript,
            "",
        ]
    )


def fetch_candidate(
    item: dict[str, Any], keyword: str, destination: Path, args: argparse.Namespace
) -> dict[str, Any]:
    payload = defuddle_extract(item["url"], args.language, args.timeout)
    transcript = transcript_from_payload(payload)
    title = str(payload.get("title") or item["title"])
    channel = str(payload.get("author") or item.get("channel") or "YouTube")
    published = normalize_date(
        payload.get("published") or item.get("published") or item.get("upload_date")
    )
    language = str(payload.get("language") or args.language)
    filename = (
        f"{safe_component(channel, fallback='YouTube频道', max_length=65, max_bytes=85)}"
        f" - {published or '日期未知'}"
        f" - {safe_component(title, fallback='未命名视频', max_length=105, max_bytes=120)}"
        f" [{item['id']}].md"
    )
    path = destination / filename
    atomic_write_text(
        path,
        render_note(
            item,
            keyword=keyword,
            title=title,
            channel=channel,
            published=published,
            language=language,
            transcript=transcript,
        ),
    )
    return {
        **item,
        "title": title,
        "channel": channel,
        "published": published,
        "language": language,
        "path": str(path.resolve()),
        "status": "created",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword", help="User-supplied research keyword or topic")
    parser.add_argument("--variant", action="append", default=[], help="Additional search query")
    parser.add_argument("--output-root", help="Local content repository; default current directory")
    parser.add_argument("--folder", default="逐字稿/主题研究", help="Repository-relative folder")
    parser.add_argument("--candidates", type=int, default=30, help="Search results per query")
    parser.add_argument("--inspect", type=int, default=15, help="Candidates to enrich and rank")
    parser.add_argument("--select", type=int, default=5, help="Accessible transcripts to select")
    parser.add_argument("--min-sources", type=int, default=3, help="Required unique channels")
    parser.add_argument("--max-per-channel", type=int, default=1, help="Selected videos per channel")
    parser.add_argument("--min-duration", type=int, default=600, help="Minimum seconds")
    parser.add_argument("--max-duration", type=int, default=21600, help="Maximum seconds")
    parser.add_argument("--min-views", type=int, default=5000, help="Minimum views")
    parser.add_argument(
        "--min-relevance",
        type=float,
        default=0.55,
        help="Minimum keyword coverage from 0 to 1",
    )
    parser.add_argument("--recency-days", type=int, default=730, help="0 disables date filtering")
    parser.add_argument("--language", default="zh-Hans", help="Preferred transcript language")
    parser.add_argument("--timeout", type=int, default=180, help="Caption extraction timeout")
    parser.add_argument("--metadata-jobs", type=int, default=4, help="Metadata requests in parallel")
    parser.add_argument("--cookies-from-browser", help="Browser[:profile] for yt-dlp")
    parser.add_argument("--dry-run", action="store_true", help="Rank only; write nothing")
    args = parser.parse_args()
    if not args.keyword.strip():
        parser.error("keyword cannot be empty")
    if not 5 <= args.candidates <= 100:
        parser.error("--candidates must be between 5 and 100")
    if not 3 <= args.inspect <= args.candidates:
        parser.error("--inspect must be between 3 and --candidates")
    if not 3 <= args.select <= 12:
        parser.error("--select must be between 3 and 12")
    if not 3 <= args.min_sources <= args.select:
        parser.error("--min-sources must be between 3 and --select")
    if not 1 <= args.max_per_channel <= 3:
        parser.error("--max-per-channel must be between 1 and 3")
    if args.min_duration < 0 or args.max_duration < args.min_duration:
        parser.error("invalid duration range")
    if not 0 <= args.min_relevance <= 1:
        parser.error("--min-relevance must be between 0 and 1")
    if not 1 <= args.metadata_jobs <= 8:
        parser.error("--metadata-jobs must be between 1 and 8")
    return args


def run(args: argparse.Namespace) -> dict[str, Any]:
    keyword = args.keyword.strip()
    queries = list(dict.fromkeys([keyword] + [value.strip() for value in args.variant if value.strip()]))
    searches = [flat_search(query, args.candidates, args) for query in queries]
    merged = merge_searches(searches)
    merged.sort(key=lambda item: preliminary_score(item, queries), reverse=True)
    inspect_items = merged[: args.inspect]
    log(f"Enriching metadata for {len(inspect_items)} candidates")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.metadata_jobs) as executor:
        enriched = list(executor.map(lambda item: enrich_one(item, args), inspect_items))

    ranked: list[dict[str, Any]] = []
    for item in enriched:
        duration = int(item.get("duration") or 0)
        views = int(item.get("view_count") or 0)
        age = days_old(str(item.get("published") or ""))
        score, reasons, relevance = final_score(item, queries, args.recency_days)
        eligible = (
            args.min_duration <= duration <= args.max_duration
            and views >= args.min_views
            and relevance >= args.min_relevance
            and (not args.recency_days or age is None or age <= args.recency_days)
        )
        item["score"] = score
        item["relevance"] = round(relevance, 4)
        item["selection_reasons"] = reasons
        item["eligible"] = eligible
        ranked.append(item)
    ranked.sort(key=lambda item: float(item["score"]), reverse=True)

    preview = [
        {
            key: item.get(key)
            for key in (
                "id",
                "title",
                "channel",
                "published",
                "duration",
                "view_count",
                "like_count",
                "score",
                "relevance",
                "eligible",
                "query_hits",
                "selection_reasons",
                "url",
            )
        }
        for item in ranked
    ]
    if args.dry_run:
        return {
            "keyword": keyword,
            "queries": queries,
            "dry_run": True,
            "candidate_count": len(merged),
            "inspected_count": len(ranked),
            "ranked_candidates": preview,
        }

    root = Path(args.output_root).expanduser().resolve() if args.output_root else Path.cwd().resolve()
    if not root.is_dir():
        raise UserFacingError(f"Output repository does not exist: {root}")
    relative_folder = Path(args.folder)
    if relative_folder.is_absolute() or ".." in relative_folder.parts:
        raise UserFacingError("--folder must be repository-relative")
    topic_slug = safe_component(keyword, fallback="未命名主题", max_length=70, max_bytes=110)
    destination = root / relative_folder / topic_slug
    destination.mkdir(parents=True, exist_ok=True)
    index_path = destination / "youtube-topic-index.json"
    index = load_json(index_path, {"schema_version": 1, "videos": {}})
    index.setdefault("videos", {})
    existing = existing_transcripts(root / "逐字稿")

    selected: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    channel_counts: dict[str, int] = {}
    for item in ranked:
        if len(selected) >= args.select:
            break
        if not item.get("eligible"):
            continue
        channel_key = str(item.get("channel_id") or normalize(str(item.get("channel") or "")))
        if channel_counts.get(channel_key, 0) >= args.max_per_channel:
            continue
        video_id = str(item["id"])
        if video_id in existing:
            record = {
                **item,
                "path": existing[video_id],
                "status": "reused",
            }
            selected.append(record)
            channel_counts[channel_key] = channel_counts.get(channel_key, 0) + 1
            index["videos"][video_id] = {
                "path": record["path"],
                "title": record["title"],
                "channel": record.get("channel"),
                "url": record["url"],
                "status": "reused",
                "updated_at": iso_now(),
            }
            continue
        log(f"Extracting transcript [{len(selected) + 1}/{args.select}]: {item['title']}")
        try:
            record = fetch_candidate(item, keyword, destination, args)
        except Exception as exc:
            failed.append(
                {
                    "id": video_id,
                    "title": item.get("title"),
                    "channel": item.get("channel"),
                    "url": item.get("url"),
                    "error": str(exc),
                }
            )
            log(f"  Failed: {exc}")
            continue
        selected.append(record)
        channel_counts[channel_key] = channel_counts.get(channel_key, 0) + 1
        existing[video_id] = record["path"]
        index["videos"][video_id] = {
            "path": record["path"],
            "title": record["title"],
            "channel": record.get("channel"),
            "url": record["url"],
            "status": "created",
            "updated_at": iso_now(),
        }

    unique_channels = sorted(
        {
            str(item.get("channel_id") or normalize(str(item.get("channel") or "")))
            for item in selected
        }
        - {""}
    )
    quality_gate_met = len(selected) >= args.select and len(unique_channels) >= args.min_sources
    research_seed = normalize(keyword) + "\n" + "\n".join(sorted(item["id"] for item in selected))
    research_id = hashlib.sha256(research_seed.encode("utf-8")).hexdigest()[:12]
    manifest = {
        "schema_version": 1,
        "keyword": keyword,
        "queries": queries,
        "topic_slug": topic_slug,
        "research_id": research_id,
        "created_at": iso_now(),
        "quality_gate_met": quality_gate_met,
        "requested_count": args.select,
        "selected_count": len(selected),
        "source_count": len(unique_channels),
        "selected": [
            {
                key: item.get(key)
                for key in (
                    "id",
                    "title",
                    "channel",
                    "channel_id",
                    "published",
                    "duration",
                    "view_count",
                    "like_count",
                    "score",
                    "selection_reasons",
                    "url",
                    "path",
                    "status",
                )
            }
            for item in selected
        ],
        "failed": failed,
        "ranked_candidates": preview,
    }
    manifest_path = destination / f"research-manifest-{research_id}.json"
    latest_path = destination / "latest-research-manifest.json"
    atomic_write_json(manifest_path, manifest)
    atomic_write_json(latest_path, manifest)
    index.update(
        {
            "schema_version": 1,
            "keyword": keyword,
            "updated_at": iso_now(),
            "latest_research_id": research_id,
        }
    )
    atomic_write_json(index_path, index)
    return {
        "keyword": keyword,
        "queries": queries,
        "output_root": str(root),
        "destination": str(destination),
        "candidate_count": len(merged),
        "inspected_count": len(ranked),
        "selected_count": len(selected),
        "source_count": len(unique_channels),
        "created_count": sum(1 for item in selected if item.get("status") == "created"),
        "reused_count": sum(1 for item in selected if item.get("status") == "reused"),
        "failed_count": len(failed),
        "quality_gate_met": quality_gate_met,
        "research_id": research_id,
        "manifest_path": str(manifest_path.resolve()),
        "selected": manifest["selected"],
        "failed": failed,
    }


def main() -> int:
    try:
        result = run(parse_args())
    except UserFacingError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {"error": str(exc), "type": type(exc).__name__},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("dry_run") or result.get("quality_gate_met") else 3


if __name__ == "__main__":
    sys.exit(main())
