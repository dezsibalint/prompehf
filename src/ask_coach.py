from openai import OpenAI

from config import VECTOR_STORE_ID_FILE, require_openai_api_key


MODEL_NAME = "gpt-5.4-mini"

COACH_INSTRUCTIONS = """
Te egy League of Legends coaching asszisztens vagy.
A válaszaidhoz az oktató YouTube-videókból készült tudásbázist használd.
Gyakorlati, játék közben alkalmazható tanácsokat adj.
Ha a tudásbázis nem tartalmaz elég információt, mondd meg, hogy erre nincs elég forrás.
Ne találj ki patch-specifikus adatokat.
""".strip()


def read_vector_store_id() -> str:
    """Read the Vector Store id saved by upload_knowledge_base.py."""
    if not VECTOR_STORE_ID_FILE.exists():
        raise RuntimeError(
            "Missing vector_store_id.txt. Run python src/upload_knowledge_base.py first."
        )

    vector_store_id = VECTOR_STORE_ID_FILE.read_text(encoding="utf-8").strip()
    if not vector_store_id:
        raise RuntimeError("vector_store_id.txt is empty.")
    return vector_store_id


def ask_question(client: OpenAI, vector_store_id: str, question: str) -> str:
    """Ask the model using file_search over the uploaded knowledge base."""
    response = client.responses.create(
        model=MODEL_NAME,
        instructions=COACH_INSTRUCTIONS,
        input=question,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
            }
        ],
    )
    return response.output_text


def main() -> None:
    client = OpenAI(api_key=require_openai_api_key())
    vector_store_id = read_vector_store_id()

    question = input("Ask a League of Legends question: ").strip()
    if not question:
        print("Please enter a question.")
        return

    answer = ask_question(client, vector_store_id, question)
    print("\nCoach answer:\n")
    print(answer)


if __name__ == "__main__":
    main()
