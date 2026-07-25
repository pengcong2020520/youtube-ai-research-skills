#!/usr/bin/env python3
"""Incrementally save a YouTube creator's latest transcripts to Obsidian."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


DEFAULT_FOLDER = "逐字稿"
INDEX_NAME = "youtube-transcripts-index.json"
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,20}$")
FRONTMATTER_ID_RE = re.compile(
    r"^youtube_video_id:\s*[\"']?([A-Za-z0-9_-]{6,20})[\"']?\s*$", re.MULTILINE
)


class UserFacingError(RuntimeError):
    """An error that should be printed without a traceback."""


@dataclass(frozen=True)
class ChannelCandidate:
    name: str
    channel_id: str
    url: str
    count: int
    score: float


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().lstrip("@").strip()
    return "".join(ch for ch in normalized if ch.isalnum())


def truncate_utf8(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore").rstrip(" .-")


def safe_component(
    value: str, *, fallback: str, max_length: int = 100, max_bytes: int = 180
) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\x00-\x1f/\\:*?\"<>|]", "-", value)
    value = re.sub(r"\s+", " ", value).strip(" .-")
    value = value or fallback
    shortened = truncate_utf8(value[:max_length].rstrip(" .-"), max_bytes)
    return shortened or fallback


def yaml_string(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def normalize_date(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return ""
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else ""


def discover_output_root(explicit_output: str | None, explicit_vault: str | None) -> Path:
    if explicit_output and explicit_vault:
        raise UserFacingError("Use either --output-root or --vault, not both.")
    if explicit_vault:
        root = Path(explicit_vault).expanduser().resolve()
        if not root.is_dir() or not (root / ".obsidian").is_dir():
            raise UserFacingError(f"Not an Obsidian vault (missing .obsidian): {root}")
        return root
    if explicit_output:
        root = Path(explicit_output).expanduser().resolve()
    else:
        root = Path.cwd().resolve()
    if not root.is_dir():
        raise UserFacingError(f"Output repository does not exist: {root}")
    return root


def relative_output_path(folder: str) -> Path:
    path = Path(folder)
    if path.is_absolute() or ".." in path.parts:
        raise UserFacingError("--folder must be a safe vault-relative path.")
    cleaned = Path(*[part for part in path.parts if part not in ("", ".")])
    if not cleaned.parts:
        raise UserFacingError("--folder cannot be empty.")
    return cleaned


def load_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": 1, "videos": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise UserFacingError(f"Cannot read transcript index {path}: {exc}") from exc
    if not isinstance(data.get("videos"), dict):
        data["videos"] = {}
    data["schema_version"] = 1
    return data


def existing_video_ids(directory: Path, index: dict[str, Any]) -> set[str]:
    ids = {str(value) for value in (index.get("videos") or {}).keys()}
    if not directory.is_dir():
        return ids
    for note in directory.glob("*.md"):
        try:
            head = note.read_text(encoding="utf-8")[:12000]
        except OSError:
            continue
        match = FRONTMATTER_ID_RE.search(head)
        if match:
            ids.add(match.group(1))
    return ids


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
    }
    cookies = cookie_tuple(args.cookies_from_browser)
    if cookies:
        options["cookiesfrombrowser"] = cookies
    options.update(extra)
    return options


def direct_channel_url(value: str) -> str | None:
    value = value.strip()
    if value.startswith("@"):
        return f"https://www.youtube.com/{value}/videos"
    if re.fullmatch(r"UC[A-Za-z0-9_-]{20,}", value):
        return f"https://www.youtube.com/channel/{value}/videos"
    parsed = urlparse(value if "://" in value else "")
    if parsed.netloc.lower().removeprefix("www.") in {"youtube.com", "m.youtube.com"}:
        return normalize_channel_url(value)
    return None


def normalize_channel_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if value.startswith("@"):
        value = f"https://www.youtube.com/{value}"
    if not value.startswith(("http://", "https://")):
        value = "https://www.youtube.com/" + value.lstrip("/")
    parsed = urlparse(value)
    path = re.sub(r"/(videos|featured|shorts|streams|playlists)$", "", parsed.path.rstrip("/"))
    return f"https://www.youtube.com{path}/videos"


def candidate_score(query: str, name: str, count: int) -> float:
    normalized_query = normalize_name(query)
    normalized_name = normalize_name(name)
    if not normalized_query or not normalized_name:
        return 0.0
    score = difflib.SequenceMatcher(None, normalized_query, normalized_name).ratio() * 50
    if normalized_query == normalized_name:
        score += 100
    elif normalized_query in normalized_name or normalized_name in normalized_query:
        score += 35
    return score + min(count, 10) * 2


def channel_candidates(entries: Iterable[dict[str, Any]], query: str) -> list[ChannelCandidate]:
    raw: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        channel_id = str(entry.get("channel_id") or entry.get("uploader_id") or "")
        name = str(entry.get("channel") or entry.get("uploader") or "").strip()
        url = str(entry.get("channel_url") or entry.get("uploader_url") or "").strip()
        if channel_id and not url:
            url = f"https://www.youtube.com/channel/{channel_id}"
        if not name or not url:
            continue
        key = (channel_id, normalize_channel_url(url))
        item = raw.setdefault(key, {"name": name, "count": 0})
        item["count"] += 1
    result = [
        ChannelCandidate(
            name=item["name"],
            channel_id=key[0],
            url=key[1],
            count=item["count"],
            score=candidate_score(query, item["name"], item["count"]),
        )
        for key, item in raw.items()
    ]
    return sorted(result, key=lambda candidate: (-candidate.score, -candidate.count, candidate.name))


def resolve_channel(
    creator: str, explicit_channel: str | None, stored_channel: str | None, args: argparse.Namespace
) -> tuple[str, str]:
    direct = direct_channel_url(explicit_channel or "") if explicit_channel else None
    if explicit_channel and not direct:
        direct = normalize_channel_url(explicit_channel)
    if direct:
        return direct, creator
    if stored_channel:
        return normalize_channel_url(stored_channel), creator
    direct = direct_channel_url(creator)
    if direct:
        return direct, creator.lstrip("@")

    from yt_dlp import YoutubeDL

    log(f"Resolving YouTube creator: {creator}")
    with YoutubeDL(ydl_options(args, extract_flat=True, playlistend=20)) as ydl:
        info = ydl.extract_info(f"ytsearch20:{creator}", download=False)
    candidates = channel_candidates((info or {}).get("entries") or [], creator)
    if not candidates:
        raise UserFacingError(f"No YouTube channel candidates found for: {creator}")

    top = candidates[0]
    normalized_query = normalize_name(creator)
    exact = [candidate for candidate in candidates if normalize_name(candidate.name) == normalized_query]
    if len(exact) == 1:
        top = exact[0]
    elif len(candidates) > 1 and top.score - candidates[1].score < 12:
        choices = [
            {"name": candidate.name, "channel_id": candidate.channel_id, "url": candidate.url}
            for candidate in candidates[:5]
        ]
        raise UserFacingError(
            "Creator name is ambiguous. Rerun with --channel URL. Candidates: "
            + json.dumps(choices, ensure_ascii=False)
        )
    return top.url, top.name


def list_latest_videos(channel_url: str, limit: int, args: argparse.Namespace) -> list[dict[str, Any]]:
    from yt_dlp import YoutubeDL

    log(f"Listing the latest {limit} regular videos: {channel_url}")
    with YoutubeDL(
        ydl_options(args, extract_flat="in_playlist", playlistend=limit, lazy_playlist=False)
    ) as ydl:
        info = ydl.extract_info(normalize_channel_url(channel_url), download=False)
    entries: list[dict[str, Any]] = []
    for entry in (info or {}).get("entries") or []:
        if not isinstance(entry, dict):
            continue
        video_id = str(entry.get("id") or "")
        if not VIDEO_ID_RE.fullmatch(video_id):
            continue
        entries.append(
            {
                "id": video_id,
                "title": str(entry.get("title") or video_id),
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "upload_date": entry.get("upload_date"),
                "timestamp": entry.get("timestamp"),
            }
        )
        if len(entries) >= limit:
            break
    return entries


def fetch_publish_date(url: str, args: argparse.Namespace) -> str:
    """Fetch full video metadata only when flat channel metadata has no date."""
    from yt_dlp import YoutubeDL

    with YoutubeDL(ydl_options(args, skip_download=True)) as ydl:
        info = ydl.extract_info(url, download=False)
    return normalize_date(
        (info or {}).get("upload_date")
        or (info or {}).get("release_date")
        or (info or {}).get("timestamp")
        or (info or {}).get("release_timestamp")
    )


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
        raise UserFacingError("Defuddle is not installed. Run through scripts/run.sh.") from exc
    except subprocess.TimeoutExpired as exc:
        raise UserFacingError(f"Defuddle timed out after {timeout}s") from exc
    if process.returncode != 0:
        detail = process.stderr.strip().splitlines()[-1] if process.stderr.strip() else "unknown error"
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
    *,
    title: str,
    creator: str,
    channel: str,
    video_id: str,
    url: str,
    published: str,
    captured: str,
    language: str,
    transcript: str,
) -> str:
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        f"creator: {yaml_string(creator)}",
        f"youtube_channel: {yaml_string(channel)}",
        f"youtube_video_id: {yaml_string(video_id)}",
        f"source: {yaml_string(url)}",
        f"published: {yaml_string(published)}",
        f"captured: {yaml_string(captured)}",
        f"transcript_language: {yaml_string(language)}",
        'transcript_source: "defuddle"',
        "tags:",
        "  - youtube-transcript",
        "---",
        "",
        f"# {title}",
        "",
        "> [!info] 视频信息",
        f"> - 博主：{creator}",
        f"> - 频道：{channel}",
        f"> - 发布日期：{published or '未知'}",
        f"> - 字幕语言：{language or '未知'}",
        f"> - [在 YouTube 观看]({url})",
        "",
        "## 逐字稿",
        "",
        transcript,
        "",
    ]
    return "\n".join(lines)


def filename_for(creator: str, title: str, published: str, video_id: str) -> str:
    creator_part = safe_component(
        creator, fallback="YouTube博主", max_length=70, max_bytes=80
    )
    title_part = safe_component(
        title, fallback="未命名视频", max_length=110, max_bytes=110
    )
    date_part = published or "日期未知"
    return f"{creator_part} - {date_part} - {title_part} [{video_id}].md"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Incrementally save a YouTube creator's latest transcripts to Obsidian."
    )
    parser.add_argument("creator", help="Creator name, @handle, channel URL, or channel ID")
    parser.add_argument("--channel", help="Explicit channel URL or @handle")
    parser.add_argument("--output-root", help="Absolute local content repository path")
    parser.add_argument("--vault", help="Absolute Obsidian vault path (validated)")
    parser.add_argument("--folder", default=DEFAULT_FOLDER, help="Repository-relative output folder")
    parser.add_argument("--limit", type=int, default=10, help="Newest regular videos to inspect")
    parser.add_argument("--language", default="zh-Hans", help="Preferred BCP 47 transcript language")
    parser.add_argument("--cookies-from-browser", help="Browser[:profile] for yt-dlp")
    parser.add_argument("--timeout", type=int, default=180, help="Defuddle timeout per video")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and preview without writing")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    if not 10 <= args.timeout <= 900:
        parser.error("--timeout must be between 10 and 900 seconds")
    return args


def run(args: argparse.Namespace) -> dict[str, Any]:
    creator = args.creator.strip()
    if not creator:
        raise UserFacingError("Creator name cannot be empty.")
    output_root = discover_output_root(args.output_root, args.vault)
    destination_root = output_root / relative_output_path(args.folder)
    creator_dir = destination_root / safe_component(
        creator, fallback="YouTube博主", max_length=80, max_bytes=180
    )
    index_path = creator_dir / INDEX_NAME
    index = load_index(index_path)
    saved_ids = existing_video_ids(creator_dir, index)

    channel_url, resolved_name = resolve_channel(
        creator, args.channel, index.get("channel_url"), args
    )
    videos = list_latest_videos(channel_url, args.limit, args)
    if not videos:
        raise UserFacingError(f"No regular videos found at {channel_url}")

    summary: dict[str, Any] = {
        "creator": creator,
        "resolved_channel_name": resolved_name,
        "channel_url": channel_url,
        "output_root": str(output_root),
        "destination": str(creator_dir),
        "inspected": len(videos),
        "created": [],
        "skipped_existing": [],
        "failed": [],
        "dry_run": bool(args.dry_run),
    }

    if args.dry_run:
        summary["videos"] = [
            {
                "id": video["id"],
                "title": video["title"],
                "url": video["url"],
                "status": "existing" if video["id"] in saved_ids else "new",
            }
            for video in videos
        ]
        return summary

    creator_dir.mkdir(parents=True, exist_ok=True)
    index.update(
        {
            "schema_version": 1,
            "creator_input": creator,
            "resolved_channel_name": resolved_name,
            "channel_url": channel_url,
            "updated_at": iso_now(),
        }
    )

    for position, video in enumerate(videos, start=1):
        video_id = video["id"]
        if video_id in saved_ids:
            summary["skipped_existing"].append(
                {"id": video_id, "title": video["title"], "url": video["url"]}
            )
            continue
        log(f"[{position}/{len(videos)}] Extracting transcript: {video['title']}")
        try:
            payload = defuddle_extract(video["url"], args.language, args.timeout)
            transcript = transcript_from_payload(payload)
            title = str(payload.get("title") or video["title"])
            channel = str(payload.get("author") or resolved_name or creator)
            published = normalize_date(
                payload.get("published") or video.get("upload_date") or video.get("timestamp")
            )
            if not published:
                published = fetch_publish_date(video["url"], args)
            language = str(payload.get("language") or args.language)
            captured = iso_now()
            filename = filename_for(creator, title, published, video_id)
            note_path = creator_dir / filename
            note = render_note(
                title=title,
                creator=creator,
                channel=channel,
                video_id=video_id,
                url=video["url"],
                published=published,
                captured=captured,
                language=language,
                transcript=transcript,
            )
            atomic_write_text(note_path, note)
            index["videos"][video_id] = {
                "filename": filename,
                "title": title,
                "url": video["url"],
                "published": published,
                "language": language,
                "captured": captured,
            }
            index["updated_at"] = iso_now()
            atomic_write_json(index_path, index)
            saved_ids.add(video_id)
            summary["created"].append(
                {"id": video_id, "title": title, "path": str(note_path), "url": video["url"]}
            )
        except Exception as exc:  # Keep a batch going; failed IDs remain retryable.
            summary["failed"].append(
                {"id": video_id, "title": video["title"], "url": video["url"], "error": str(exc)}
            )
            log(f"  Failed: {exc}")

    atomic_write_json(index_path, index)
    return summary


def main(argv: list[str] | None = None) -> int:
    try:
        summary = run(parse_args(argv))
    except UserFacingError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
