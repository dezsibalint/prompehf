from openai import OpenAI

from config import (
    DATA_PROCESSED_DIR,
    VECTOR_STORE_ID_FILE,
    VECTOR_STORE_NAME,
    require_openai_api_key,
)


def get_processed_files() -> list:
    """Return processed transcript text files."""
    return sorted(DATA_PROCESSED_DIR.glob("*.txt"))


def upload_files(client: OpenAI, file_paths: list) -> list[str]:
    """Upload local text files to OpenAI and return their file ids."""
    file_ids = []

    for file_path in file_paths:
        print(f"Uploading file: {file_path.name}")
        with file_path.open("rb") as file:
            uploaded_file = client.files.create(
                file=file,
                purpose="assistants",
            )
        file_ids.append(uploaded_file.id)
        print(f"Uploaded {file_path.name} as {uploaded_file.id}")

    return file_ids


def main() -> None:
    processed_files = get_processed_files()
    if not processed_files:
        print("No processed transcript files found in data/processed.")
        print("Run python src/preprocess_transcripts.py first.")
        return

    client = OpenAI(api_key=require_openai_api_key())

    print(f"Creating Vector Store: {VECTOR_STORE_NAME}")
    vector_store = client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"Vector Store created: {vector_store.id}")

    file_ids = upload_files(client, processed_files)

    print("Adding uploaded files to the Vector Store...")
    batch = client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store.id,
        file_ids=file_ids,
    )

    print(f"Batch status: {batch.status}")
    print(f"File counts: {batch.file_counts}")

    VECTOR_STORE_ID_FILE.write_text(vector_store.id, encoding="utf-8")
    print(f"Saved Vector Store id to {VECTOR_STORE_ID_FILE}")


if __name__ == "__main__":
    main()
