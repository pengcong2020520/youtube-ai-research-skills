#!/usr/bin/env python3
"""Fetch every source in a built-in transcript collection."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CATALOG = SCRIPT_DIR.parent / "references/ai-sources.json"
SINGLE_FETCHER = SCRIPT_DIR / "fetch_transcripts.py"


class CollectionError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_collection(path: Path, collection_id: str) -> dict[str, Any]:
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CollectionError(f"Collection catalog not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CollectionError(f"Invalid collection catalog: {exc}") from exc
    collection = (catalog.get("collections") or {}).get(collection_id)
    if not collection:
        available = sorted((catalog.get("collections") or {}).keys())
        raise CollectionError(
            f"Unknown collection {collection_id!r}. Available: {', '.join(available)}"
        )
    sources = collection.get("sources") or []
    if not sources:
        raise CollectionError(f"Collection {collection_id!r} has no sources.")
    ids = [source.get("id") for source in sources]
    urls = [source.get("channel_url") for source in sources]
    if any(not value for value in ids + urls):
        raise CollectionError("Every source needs id and channel_url.")
    if len(ids) != len(set(ids)) or len(urls) != len(set(urls)):
        raise CollectionError("Collection source IDs and channel URLs must be unique.")
    return collection


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a built-in YouTube transcript collection.")
    parser.add_argument("collection", help="Collection ID, for example ai-high-quality")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Collection catalog JSON")
    parser.add_argument("--output-root", help="Absolute local content repository path")
    parser.add_argument("--vault", help="Absolute Obsidian vault path")
    parser.add_argument("--folder", default="逐字稿", help="Repository-relative output folder")
    parser.add_argument("--limit", type=int, default=10, help="Newest videos per source")
    parser.add_argument("--jobs", type=int, default=3, help="Sources to fetch concurrently")
    parser.add_argument("--only", action="append", help="Fetch only this source ID; repeatable")
    parser.add_argument("--timeout", type=int, default=180, help="Defuddle timeout per video")
    parser.add_argument("--cookies-from-browser", help="Browser[:profile] for yt-dlp")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args(argv)
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be between 1 and 100")
    if not 1 <= args.jobs <= 12:
        parser.error("--jobs must be between 1 and 12")
    if args.output_root and args.vault:
        parser.error("Use either --output-root or --vault, not both")
    return args


def build_command(source: dict[str, Any], args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(SINGLE_FETCHER),
        str(source["display_name"]),
        "--channel",
        str(source["channel_url"]),
        "--limit",
        str(args.limit),
        "--language",
        str(source.get("preferred_language") or "zh-Hans"),
        "--folder",
        args.folder,
        "--timeout",
        str(args.timeout),
    ]
    if args.output_root:
        command.extend(["--output-root", args.output_root])
    elif args.vault:
        command.extend(["--vault", args.vault])
    if args.cookies_from_browser:
        command.extend(["--cookies-from-browser", args.cookies_from_browser])
    if args.dry_run:
        command.append("--dry-run")
    return command


def fetch_source(source: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    source_id = str(source["id"])
    log(f"[{source_id}] Starting {source['display_name']}")
    process = subprocess.run(
        build_command(source, args), capture_output=True, text=True, check=False
    )
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        payload = {
            "error": "Fetcher returned invalid JSON",
            "stdout": process.stdout[-2000:],
        }
    result = {
        "source_id": source_id,
        "display_name": source["display_name"],
        "channel_url": source["channel_url"],
        "returncode": process.returncode,
        "result": payload,
    }
    if process.returncode != 0 and process.stderr.strip():
        result["stderr"] = process.stderr.strip()[-4000:]
    created = len(payload.get("created") or []) if isinstance(payload, dict) else 0
    skipped = len(payload.get("skipped_existing") or []) if isinstance(payload, dict) else 0
    failed = len(payload.get("failed") or []) if isinstance(payload, dict) else 0
    log(f"[{source_id}] Done: created={created}, skipped={skipped}, failed={failed}")
    return result


def run(args: argparse.Namespace) -> dict[str, Any]:
    collection = load_collection(Path(args.catalog).expanduser().resolve(), args.collection)
    sources = list(collection["sources"])
    if args.only:
        wanted = set(args.only)
        known = {str(source["id"]) for source in sources}
        missing = sorted(wanted - known)
        if missing:
            raise CollectionError(f"Unknown source IDs: {', '.join(missing)}")
        sources = [source for source in sources if source["id"] in wanted]

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(args.jobs, len(sources))) as executor:
        futures = {executor.submit(fetch_source, source, args): source for source in sources}
        for future in as_completed(futures):
            results.append(future.result())
    order = {source["id"]: index for index, source in enumerate(sources)}
    results.sort(key=lambda item: order[item["source_id"]])

    created_paths: list[str] = []
    skipped_count = 0
    transcript_failures: list[dict[str, Any]] = []
    source_failures: list[dict[str, Any]] = []
    for item in results:
        payload = item["result"] if isinstance(item["result"], dict) else {}
        created_paths.extend(
            entry["path"] for entry in payload.get("created") or [] if entry.get("path")
        )
        skipped_count += len(payload.get("skipped_existing") or [])
        transcript_failures.extend(
            {"source_id": item["source_id"], **failure}
            for failure in payload.get("failed") or []
        )
        if item["returncode"] != 0 or payload.get("error"):
            source_failures.append(
                {
                    "source_id": item["source_id"],
                    "error": payload.get("error") or f"exit {item['returncode']}",
                }
            )
    return {
        "collection": args.collection,
        "description": collection.get("description"),
        "source_count": len(sources),
        "limit_per_source": args.limit,
        "dry_run": bool(args.dry_run),
        "created_count": len(created_paths),
        "created_paths": created_paths,
        "skipped_existing_count": skipped_count,
        "transcript_failures": transcript_failures,
        "source_failures": source_failures,
        "sources": results,
    }


def main(argv: list[str] | None = None) -> int:
    try:
        summary = run(parse_args(argv))
    except CollectionError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(
            json.dumps(
                {"error": str(exc), "type": type(exc).__name__}, ensure_ascii=False, indent=2
            )
        )
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 2 if summary["source_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
