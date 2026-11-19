
import csv
import time
from pathlib import Path

import psycopg
from sentence_transformers import SentenceTransformer

from classifier import classify_review, PREDICATE


DB_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "dbname": "semantic_filter",
    "user": "postgres",
    "password": "postgres",
}

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

SMALL_MODEL = "llama3.2:3b"
LARGE_MODEL = "llama3:latest"

# Tier 1 classification thresholds are not calibrated.
# All reviews currently proceed to Tier 2.
LOW_THRESHOLD = None
HIGH_THRESHOLD = None

# Diagnostic routing only.
# Review 4 is escalated because the models previously disagreed.
# This is NOT confidence-based escalation.
DIAGNOSTIC_ESCALATION_IDS = {4}

OUTPUT_PATH = Path(
    "experiments/cascade_three_tier_results.csv"
)


def get_predicate_embedding(model, predicate):
    embedding = model.encode(predicate).tolist()
    return "[" + ",".join(map(str, embedding)) + "]"


def fetch_reviews_with_similarity(predicate_vector):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    review_text,
                    1 - (embedding <=> %s::vector)
                        AS similarity
                FROM reviews
                WHERE embedding IS NOT NULL
                ORDER BY id
                """,
                (predicate_vector,)
            )
            return cur.fetchall()


def tier1_decision(similarity):
    if LOW_THRESHOLD is None or HIGH_THRESHOLD is None:
        return None

    if similarity <= LOW_THRESHOLD:
        return False

    if similarity >= HIGH_THRESHOLD:
        return True

    return None


def should_escalate(review_id):
    # Temporary diagnostic policy.
    # Replace with calibrated confidence routing in future work.
    return review_id in DIAGNOSTIC_ESCALATION_IDS


def run_cascade():
    pipeline_start = time.perf_counter()

    print("=== CMSC724 Three-Tier Semantic Filtering ===")
    print(f"Predicate: {PREDICATE}")
    print(f"Tier 2: {SMALL_MODEL}")
    print(f"Tier 3: {LARGE_MODEL}")
    print("Routing policy: diagnostic escalation")

    print("\nLoading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    predicate_vector = get_predicate_embedding(
        embedding_model,
        PREDICATE
    )

    reviews = fetch_reviews_with_similarity(
        predicate_vector
    )

    results = []

    tier1_count = 0
    tier2_calls = 0
    tier3_calls = 0

    tier2_total_time = 0.0
    tier3_total_time = 0.0

    for review_id, review_text, similarity in reviews:
        print(f"\n--- Review {review_id} ---")
        print(f"Review: {review_text}")
        print(f"Tier 1 similarity: {similarity:.4f}")

        decision = tier1_decision(similarity)

        tier2_result = None
        tier3_result = None

        tier2_time = 0.0
        tier3_time = 0.0

        if decision is not None:
            # Tier 1 confidently classified the review.
            final_classification = decision
            final_tier = "Tier 1"
            tier1_count += 1

            print("Classified by Tier 1")

        else:
            # Tier 2: Small LLM
            print("Tier 1 uncertain: forwarding to Tier 2")

            tier2_result, tier2_time = classify_review(
                review_text,
                PREDICATE,
                model_name=SMALL_MODEL
            )

            tier2_calls += 1
            tier2_total_time += tier2_time

            print(f"Tier 2 prediction: {tier2_result}")
            print(f"Tier 2 request time: {tier2_time:.3f}s")

            final_classification = tier2_result
            final_tier = "Tier 2"

            # Tier 3: Diagnostic escalation
            if should_escalate(review_id):
                print("Diagnostic escalation to Tier 3")

                tier3_result, tier3_time = classify_review(
                    review_text,
                    PREDICATE,
                    model_name=LARGE_MODEL
                )

                tier3_calls += 1
                tier3_total_time += tier3_time

                print(f"Tier 3 prediction: {tier3_result}")
                print(f"Tier 3 request time: {tier3_time:.3f}s")

                # For this test, Tier 3 provides the final
                # prediction for escalated reviews.
                final_classification = tier3_result
                final_tier = "Tier 3"

        print(f"Final classification: {final_classification}")
        print(f"Final tier: {final_tier}")

        results.append({
            "review_id": review_id,
            "review_text": review_text,
            "predicate": PREDICATE,
            "similarity": round(similarity, 4),
            "tier2_prediction": tier2_result,
            "tier3_prediction": tier3_result,
            "final_classification": final_classification,
            "final_tier": final_tier,
            "tier2_time_seconds": round(tier2_time, 3),
            "tier3_time_seconds": round(tier3_time, 3),
            "escalated": final_tier == "Tier 3",
        })

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
                "review_id",
                "review_text",
                "predicate",
                "similarity",
                "tier2_prediction",
                "tier3_prediction",
                "final_classification",
                "final_tier",
                "tier2_time_seconds",
                "tier3_time_seconds",
                "escalated",
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    total_pipeline_time = (
        time.perf_counter() - pipeline_start
    )

    print("\n=== Experiment Summary ===")
    print(f"Reviews processed: {len(reviews)}")
    print(f"Tier 1 classifications: {tier1_count}")
    print(f"Tier 2 calls: {tier2_calls}")
    print(f"Tier 3 calls: {tier3_calls}")
    print(f"Total LLM calls: {tier2_calls + tier3_calls}")

    print(
        f"Tier 2 total request time: "
        f"{tier2_total_time:.3f}s"
    )

    print(
        f"Tier 3 total request time: "
        f"{tier3_total_time:.3f}s"
    )

    print(
        f"Total pipeline time: "
        f"{total_pipeline_time:.3f}s"
    )

    print(f"Results saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    run_cascade()
