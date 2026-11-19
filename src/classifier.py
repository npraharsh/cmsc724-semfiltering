
import time
import psycopg
import requests

MODEL_NAME = "llama3.2:3b"
OLLAMA_URL = "http://localhost:11434/api/generate"

PREDICATE = "The reviewer enjoyed the movie"


def classify_review(review, predicate, model_name=MODEL_NAME):
    prompt = f"""
You are a semantic filtering classifier.

Determine whether the following review satisfies the predicate.

Predicate: {predicate}
Review: {review}

Return exactly one word: TRUE or FALSE.
Do not provide an explanation.
"""

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        },
        timeout=120
    )

    response.raise_for_status()

    elapsed = time.perf_counter() - start

    answer = response.json()["response"].strip().upper()
    answer = answer.rstrip(".")

    if answer not in ("TRUE", "FALSE"):
        raise ValueError(f"Unexpected model response: {answer}")

    return answer == "TRUE", elapsed


def main():
    conn = psycopg.connect(
        host="localhost",
        port=5433,
        dbname="semantic_filter",
        user="postgres",
        password="postgres"
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, review_text FROM reviews ORDER BY id"
            )
            reviews = cur.fetchall()

    total_time = 0

    print(f"Model: {MODEL_NAME}")
    print(f"Predicate: {PREDICATE}")

    for review_id, review_text in reviews:
        classification, elapsed = classify_review(
            review_text, PREDICATE
        )

        total_time += elapsed

        print(f"\nReview ID: {review_id}")
        print(f"Review: {review_text}")
        print(f"Classification: {classification}")
        print(f"Inference time: {elapsed:.3f} seconds")

    print("\n--- Summary ---")
    print(f"Total reviews: {len(reviews)}")
    print(f"LLM calls: {len(reviews)}")
    print(f"Total inference time: {total_time:.3f} seconds")


if __name__ == "__main__":
    main()
