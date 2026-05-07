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
    "LoL beginner guide",
    "LoL advanced guide",
    "League of Legends macro coaching",
    "League of Legends jungle coaching",
    "League of Legends laning guide",
    "LoL top lane guide",
    "LoL mid lane guide",
    "LoL ADC guide",
    "LoL support guide",
    "LoL warding guide",
    "LoL roaming guide",
    "LoL recall timing",
    "LoL objective control",
]
DEFAULT_EXCLUDE_TERMS = [
    "2xko",
    "tft",
    "teamfight tactics",
    "set 17",
    "trailer",
    "spotlight",
    "cinematic",
    "skin",
    "skins",
    "wild rift",
]


class YouTubeApiError(RuntimeError):
    """Small wrapper so the script can handle quota errors gracefully."""

    def __init__(self, status_code: int, message: str, reason: str = "") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason

    def is_quota_exceeded(self) -> bool:
        return self.reason == "quotaExceeded"


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
        default=5_000,
        help="Only include videos with at least this many views.",
    )
    parser.add_argument(
        "--queries",
        nargs="+",
        default=DEFAULT_QUERIES,
        help="Search queries to use. Put each query in quotes.",
    )
    parser.add_argument(
        "--exclude-terms",
        nargs="+",
        default=DEFAULT_EXCLUDE_TERMS,
        help="Skip videos whose title contains any of these terms.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output file for discovered YouTube URLs.",
    )
    output_mode = parser.add_mutually_exclusive_group()
    output_mode.add_argument(
        "--append",
        action="store_true",
        help="Append unique URLs to the output file. This is the default behavior.",
    )
    output_mode.add_argument(
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
    parser.add_argument(
        "--caption",
        choices=["closedCaption", "any"],
        default="closedCaption",
        help="Caption filter for YouTube search. Use 'any' to discover more candidates.",
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
        reason = ""
        message = details

        try:
            error_data = json.loads(details)
            api_error = error_data.get("error", {})
            message = api_error.get("message", details)
            errors = api_error.get("errors", [])
            if errors:
                reason = errors[0].get("reason", "")
        except json.JSONDecodeError:
            pass

        raise YouTubeApiError(error.code, message, reason) from error
    except URLError as error:
        raise RuntimeError(f"Could not connect to YouTube API: {error}") from error


def search_video_ids(
    api_key: str,
    query: str,
    published_after: str,
    max_pages: int,
    region: str,
    language: str,
    caption: str,
) -> tuple[list[str], bool]:
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
            "maxResults": 50,
            "regionCode": region,
            "relevanceLanguage": language,
        }

        if caption != "any":
            params["videoCaption"] = caption

        if next_page_token:
            params["pageToken"] = next_page_token

        try:
            data = youtube_get(SEARCH_URL, params)
        except YouTubeApiError as error:
            if error.is_quota_exceeded():
                print("YouTube API quota exceeded while searching. Stopping early.")
                return video_ids, True
            raise

        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return video_ids, False


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


def title_contains_excluded_term(video: dict[str, Any], exclude_terms: list[str]) -> bool:
    title = video["title"].lower()
    return any(term.lower() in title for term in exclude_terms)


def make_quota_limited_video(video_id: str) -> dict[str, Any]:
    return {
        "id": video_id,
        "title": "Unknown title because quota was exceeded",
        "channel": "Unknown channel",
        "published_at": "",
        "view_count": 0,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def discover_videos(args: argparse.Namespace) -> list[dict[str, Any]]:
    api_key = require_youtube_api_key()
    published_after = months_ago_as_iso(args.months)

    print(f"Searching videos published after: {published_after}")
    print(f"Target video count: {args.limit}")

    candidate_ids = []
    seen_ids = set()
    quota_exceeded = False

    for query in args.queries:
        print(f"Searching query: {query}")
        try:
            query_ids, query_hit_quota = search_video_ids(
                api_key=api_key,
                query=query,
                published_after=published_after,
                max_pages=args.max_pages_per_query,
                region=args.region,
                language=args.language,
                caption=args.caption,
            )
        except YouTubeApiError as error:
            print(f"Skipping query because YouTube API returned an error: {error}")
            continue

        for video_id in query_ids:
            if video_id not in seen_ids:
                candidate_ids.append(video_id)
                seen_ids.add(video_id)

        if query_hit_quota:
            quota_exceeded = True
            break

    print(f"Found {len(candidate_ids)} unique candidate videos.")

    if not candidate_ids:
        return []

    try:
        videos = fetch_video_details(api_key, candidate_ids)
    except YouTubeApiError as error:
        if error.is_quota_exceeded():
            print("YouTube API quota exceeded before video statistics could be fetched.")
            print("Saving discovered URLs without popularity filtering.")
            return [make_quota_limited_video(video_id) for video_id in candidate_ids[: args.limit]]
        raise

    normalized_videos = [normalize_video(video) for video in videos]
    popular_videos = [
        video
        for video in normalized_videos
        if video["view_count"] >= args.min_views
        and not title_contains_excluded_term(video, args.exclude_terms)
    ]
    popular_videos.sort(key=lambda video: video["view_count"], reverse=True)

    if quota_exceeded:
        print("Results are partial because the YouTube API quota was reached.")

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
            "YouTube API pagination, daily quota, captions, and search ranking can limit results."
        )


if __name__ == "__main__":
    main()
