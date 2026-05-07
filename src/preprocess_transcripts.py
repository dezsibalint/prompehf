import re
import textwrap

from config import DATA_PROCESSED_DIR, DATA_RAW_DIR


def clean_transcript(text: str) -> str:
    """Remove common transcript noise and normalize whitespace."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\[(music|applause)\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def preprocess_file(input_path) -> None:
    raw_text = input_path.read_text(encoding="utf-8")
    cleaned_text = clean_transcript(raw_text)

    output_path = DATA_PROCESSED_DIR / input_path.name
    output_path.write_text(textwrap.fill(cleaned_text, width=100), encoding="utf-8")
    print(f"Processed: {input_path.name} -> {output_path}")


def main() -> None:
    raw_files = sorted(DATA_RAW_DIR.glob("*.txt"))
    if not raw_files:
        print("No raw transcript files found in data/raw.")
        return

    for input_path in raw_files:
        preprocess_file(input_path)


if __name__ == "__main__":
    main()
