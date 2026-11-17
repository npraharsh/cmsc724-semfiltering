
import psycopg
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

predicate = "The reviewer enjoyed the movie"

# Generate embedding for the predicate
predicate_embedding = model.encode(predicate).tolist()
vector = "[" + ",".join(map(str, predicate_embedding)) + "]"

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
            """
            SELECT
                id,
                review_text,
                1 - (embedding <=> %s::vector) AS similarity
            FROM reviews
            ORDER BY similarity DESC
            """,
            (vector,)
        )

        results = cur.fetchall()

        for review_id, review_text, similarity in results:
            print(f"\nReview ID: {review_id}")
            print(f"Review: {review_text}")
            print(f"Similarity: {similarity:.4f}")

conn.close()
