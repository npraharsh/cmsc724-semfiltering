
import csv
from pathlib import Path

import psycopg

from classifier import classify_review, PREDICATE


MODELS = [
    "llama3.2:3b",
    "llama3:latest"
]

DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "semantic_filter",
    "user": "postgres",
    "password": "postgres"
}

OUTPUT_PATH = Path("experiments/model_comparison.csv")


def get_reviews():
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, review_text
                FROM reviews
                ORDER BY id
                """
            )
            return cur.fetchall()


def compare_models():
    reviews = get_reviews()
    results = []

    print("=== Tier 2 vs Tier 3 Model Comparison ===")
    print(f"Predicate: {PREDICATE}")
    print(f"Reviews: {len(reviews)}")

    for model in MODELS:
        print(f"\n--- Model: {model} ---")

        total_time = 0.0

        for review_id, review_text in reviews:
            classification, elapsed = classify_review(
                review_text,
                PREDICATE,
                model_name=model
            )

            total_time += elapsed

            print(f"\nReview ID: {review_id}")
            print(f"Review: {review_text}")
            print(f"Classification: {classification}")
            print(f"Request time: {elapsed:.3f} seconds")

            results.append({
                "model": model,
                "review_id": review_id,
                "review_text": review_text,
                "predicate": PREDICATE,
                "classification": classification,
                "request_time_seconds": round(elapsed, 3)
            })

        print(
            f"\nTotal request time for {model}: "
            f"{total_time:.3f} seconds"
        )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_PATH.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "model",
                "review_id",
                "review_text",
                "predicate",
                "classification",
                "request_time_seconds"
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n=== Comparison Complete ===")
    print(f"Reviews per model: {len(reviews)}")
    print(f"Models evaluated: {len(MODELS)}")
    print(f"Total LLM calls: {len(results)}")
    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    compare_models()
