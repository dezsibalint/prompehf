from pathlib import Path
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

from config import DATA_RAW_DIR, PROJECT_ROOT


VIDEO_URLS_FILE = PROJECT_ROOT / "examples" / "video_urls.txt"


def read_video_urls(file_path: Path) -> list[str]:
    """Read non-empty, non-comment lines from the URL list."""
    if not file_path.exists():
        print(f"Missing file: {file_path}")
        return []

    urls = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        cleaned_line = line.strip()
        if cleaned_line and not cleaned_line.startswith("#"):
            urls.append(cleaned_line)
    return urls


def extract_video_id(url: str) -> str | None:
    """Extract a YouTube video id from common YouTube URL formats."""
    parsed_url = urlparse(url)

    if parsed_url.netloc in {"youtu.be", "www.youtu.be"}:
        return parsed_url.path.strip("/") or None

    if "youtube.com" in parsed_url.netloc:
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query).get("v", [None])[0]

        path_parts = [part for part in parsed_url.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            return path_parts[1]

    return None


def fetch_english_transcript(video_id: str) -> list[dict]:
    """Fetch an English transcript while staying compatible with API versions."""
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
    except AttributeError:
        api = YouTubeTranscriptApi()
        fetched_transcript = api.fetch(video_id, languages=["en"])
        if hasattr(fetched_transcript, "to_raw_data"):
            return fetched_transcript.to_raw_data()
        return [{"text": item.text} for item in fetched_transcript]


def save_transcript(video_id: str, transcript: list[dict]) -> None:
    """Save transcript text lines to data/raw/video_id.txt."""
    output_path = DATA_RAW_DIR / f"{video_id}.txt"
    lines = [item.get("text", "").strip() for item in transcript if item.get("text")]
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved transcript: {output_path}")


def download_transcript_for_url(url: str) -> None:
    video_id = extract_video_id(url)
    if not video_id:
        print(f"Could not extract video id from URL: {url}")
        return

    try:
        transcript = fetch_english_transcript(video_id)
        save_transcript(video_id, transcript)
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as error:
        print(f"Could not download English transcript for {video_id}: {error}")
    except Exception as error:
        print(f"Unexpected error while processing {video_id}: {error}")


def main() -> None:
    urls = read_video_urls(VIDEO_URLS_FILE)
    if not urls:
        print("No video URLs found. Add URLs to examples/video_urls.txt first.")
        return

    for url in urls:
        download_transcript_for_url(url)


if __name__ == "__main__":
    main()
