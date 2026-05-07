import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from config import PROJECT_ROOT, require_youtube_api_key


SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "examples" / "discovered_video_urls.txt"
DEFAULT_QUERIES = [
    "League of Legends guide",
    "League of Legends coaching",
    "LoL macro guide",
    "LoL jungle guide",
    "LoL wave management",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover recent popular League of Legends guide videos on YouTube."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of video URLs to save.",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Only include videos published in the last N months.",
    )
    parser.add_argument(
        "--min-views",
        type=int,
        default=50_000,
        help="Only include videos with at least this many views.",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        default=DEFAULT_QUERIES,
        help="Search queries to use. Put each query in quotes.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output file for discovered YouTube URLs.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file instead of appending unique URLs.",
    )
    parser.add_argument(
        "--max-pages-per-query",
        type=int,
        default=10,
        help="Maximum YouTube search result pages to read for each query.",
    )
    parser.add_argument(
        "--region",
        default="US",
        help="YouTube region code used for search ranking.",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Preferred result language.",
    )
    return parser.parse_args()


def months_ago_as_iso(months: int) -> str:
    """Return an ISO timestamp for approximately N months ago."""
    days = max(months, 1) * 30
    published_after = datetime.now(timezone.utc) - timedelta(days=days)
    return published_after.isoformat().replace("+00:00", "Z")


def youtube_get(url: str, params: dict[str, Any]) -> dict[str, Any]:
    request_url = f"{url}?{urlencode(params)}"

    try:
        with urlopen(request_url, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"YouTube API request failed with HTTP {error.code}: {details}") from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to YouTube API: {error}") from error


def search_video_ids(
    api_key: str,
    query: str,
    published_after: str,
    max_pages: int,
    region: str,
    language: str,
) -> list[str]:
    """Search YouTube and return candidate video ids."""
    video_ids = []
    next_page_token = None

    for _ in range(max_pages):
        params = {
            "key": api_key,
            "part": "snippet",
            "type": "video",
            "q": query,
            "order": "viewCount",
            "publishedAfter": published_after,
            "videoCaption": "closedCaption",
            "maxResults": 50,
            "regionCode": region,
            "relevanceLanguage": language,
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        data = youtube_get(SEARCH_URL, params)
        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def fetch_video_details(api_key: str, video_ids: list[str]) -> list[dict[str, Any]]:
    """Fetch statistics and snippets for candidate videos."""
    videos = []

    for chunk in chunked(video_ids, 50):
        params = {
            "key": api_key,
            "part": "snippet,statistics",
            "id": ",".join(chunk),
        }
        data = youtube_get(VIDEOS_URL, params)
        videos.extend(data.get("items", []))

    return videos


def normalize_video(video: dict[str, Any]) -> dict[str, Any]:
    statistics = video.get("statistics", {})
    snippet = video.get("snippet", {})
    view_count = int(statistics.get("viewCount", 0))

    return {
        "id": video["id"],
        "title": snippet.get("title", "Untitled video"),
        "channel": snippet.get("channelTitle", "Unknown channel"),
        "published_at": snippet.get("publishedAt", ""),
        "view_count": view_count,
        "url": f"https://www.youtube.com/watch?v={video['id']}",
    }


def discover_videos(args: argparse.Namespace) -> list[dict[str, Any]]:
    api_key = require_youtube_api_key()
    published_after = months_ago_as_iso(args.months)

    print(f"Searching videos published after: {published_after}")
    print(f"Target video count: {args.limit}")

    candidate_ids = []
    seen_ids = set()

    for query in args.queries:
        print(f"Searching query: {query}")
        query_ids = search_video_ids(
            api_key=api_key,
            query=query,
            published_after=published_after,
            max_pages=args.max_pages_per_query,
            region=args.region,
            language=args.language,
        )

        for video_id in query_ids:
            if video_id not in seen_ids:
                candidate_ids.append(video_id)
                seen_ids.add(video_id)

    print(f"Found {len(candidate_ids)} unique candidate videos.")

    videos = fetch_video_details(api_key, candidate_ids)
    normalized_videos = [normalize_video(video) for video in videos]
    popular_videos = [
        video for video in normalized_videos if video["view_count"] >= args.min_views
    ]
    popular_videos.sort(key=lambda video: video["view_count"], reverse=True)

    return popular_videos[: args.limit]


def read_existing_urls(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()

    urls = set()
    for line in output_path.read_text(encoding="utf-8").splitlines():
        cleaned_line = line.strip()
        if cleaned_line and not cleaned_line.startswith("#"):
            urls.add(cleaned_line)
    return urls


def save_video_urls(videos: list[dict[str, Any]], output_path: Path, overwrite: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing_urls = set() if overwrite else read_existing_urls(output_path)
    new_videos = [video for video in videos if video["url"] not in existing_urls]
    needs_separator = (
        not overwrite
        and output_path.exists()
        and output_path.stat().st_size > 0
        and not output_path.read_text(encoding="utf-8").endswith("\n")
    )

    mode = "w" if overwrite else "a"
    with output_path.open(mode, encoding="utf-8") as file:
        if needs_separator:
            file.write("\n")

        if overwrite:
            file.write("# Automatically discovered YouTube video URLs\n")
            file.write("# Generated by src/discover_youtube_guides.py\n")

        for video in new_videos:
            file.write(f"{video['url']}\n")

    print(f"Saved {len(new_videos)} new URLs to {output_path}")

    if len(videos) == 0:
        print("No videos matched the filters. Try lowering --min-views or increasing --months.")
    elif len(videos) < 10:
        print("Only a few videos matched. The transcript download step may filter out more.")


def print_preview(videos: list[dict[str, Any]]) -> None:
    print("\nTop discovered videos:")
    for video in videos[:10]:
        print(
            f"- {video['title']} | {video['view_count']} views | "
            f"{video['channel']} | {video['url']}"
        )


def main() -> None:
    args = parse_args()
    videos = discover_videos(args)
    print_preview(videos)
    save_video_urls(videos, args.output, args.overwrite)

    if len(videos) < args.limit:
        print(
            f"Requested {args.limit} videos, but only {len(videos)} matched the filters. "
            "YouTube API pagination, quota, captions, and search ranking can limit results."
        )


if __name__ == "__main__":
    main()
