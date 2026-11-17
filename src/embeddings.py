
import psycopg
from sentence_transformers import SentenceTransformer

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Connect to our separate PostgreSQL database
conn = psycopg.connect(
    host="localhost",
    port=5433,
    dbname="semantic_filter",
    user="postgres",
    password="postgres"
)

with conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, review_text FROM reviews")
        reviews = cur.fetchall()

        for review_id, review_text in reviews:
            embedding = model.encode(review_text).tolist()

            # Convert the vector into pgvector's text format
            vector = "[" + ",".join(map(str, embedding)) + "]"

            cur.execute(
                """
                UPDATE reviews
                SET embedding = %s::vector
                WHERE id = %s
                """,
                (vector, review_id)
            )

            print(f"Generated embedding for review {review_id}")

conn.close()

print("All embeddings stored successfully!")
