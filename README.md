
# LLM Cascade-Based Semantic Filtering in PostgreSQL

CMSC724 – Database Management Systems

## Project Overview

This project investigates how semantic filtering can be implemented and optimized within PostgreSQL using a cascade of language models.

Traditional SQL filtering relies on structured conditions, while semantic filtering allows users to evaluate natural-language predicates over text stored in a database.

Our proposed system uses three classification tiers:

1. **Tier 1: Embeddings + pgvector** — Computes semantic similarity between text values and natural-language predicates.
2. **Tier 2: Small LLM** — Evaluates cases where embedding similarity is insufficient for confident classification.
3. **Tier 3: Large LLM** — Handles difficult cases that remain uncertain after the first two tiers.

We also plan to investigate confidence calibration, batching, caching, and PostgreSQL query execution behavior.

## Current Implementation Progress

**Tier 1 — Partially Implemented**

We have completed the initial embedding generation, storage, and similarity search functionality.

- Created a PostgreSQL 17 database using Docker.
- Enabled the pgvector extension.
- Created a `reviews` table containing sample movie reviews.
- Generated 384-dimensional embeddings using `all-MiniLM-L6-v2`.
- Stored the embeddings in PostgreSQL.
- Implemented cosine similarity searches using pgvector.

Similarity-based Boolean classification and confidence thresholds have not yet been implemented.

**Preliminary Observation**

When evaluating the predicate "The reviewer enjoyed the movie," the review "The movie was boring and I almost fell asleep" received the highest similarity score of 0.5217.

This demonstrates an important limitation: embedding similarity does not necessarily indicate whether a text value satisfies a natural-language predicate.

## Prerequisites

Install the following software:

- Python 3.13 or a compatible Python version
- Docker Desktop
- Git

Ollama will also be used in later stages for local LLM inference.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/npraharsh/cmsc724-semfiltering.git
cd cmsc724-semfiltering
```

### 2. Start PostgreSQL

Make sure Docker Desktop is running.

```bash
docker compose up -d
```

This starts a separate PostgreSQL 17 container with pgvector available.

Database configuration:

- Container: `cmsc724-project-db`
- Database: `semantic_filter`
- Username: `postgres`
- Password: `postgres`
- Local port: `5433`

The current configuration uses a simple password for local development only. Do not expose this database publicly.

### 3. Initialize the Database

Run the following command from PowerShell:

```powershell
Get-Content sql/setup.sql | docker exec -i cmsc724-project-db psql -v ON_ERROR_STOP=1 -U postgres -d semantic_filter
```

This creates the `reviews` table, enables pgvector, and inserts five sample movie reviews.

The setup script can be executed multiple times without inserting duplicate copies of the sample reviews.

### 4. Set Up the Python Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The virtual environment keeps the project's Python dependencies separate from other Python installations.

### 5. Generate and Store Embeddings

```powershell
python src/embeddings.py
```

This script:

1. Connects to PostgreSQL on port `5433`.
2. Retrieves the reviews from the database.
3. Generates 384-dimensional embeddings using `all-MiniLM-L6-v2`.
4. Stores the embeddings in PostgreSQL using pgvector.

The embedding model will be downloaded automatically on first use.

### 6. Run a Similarity Search

```powershell
python src/similarity.py
```

The script compares each stored review against the natural-language predicate:

"The reviewer enjoyed the movie"

It uses pgvector's cosine-distance operator (`<=>`) and converts the result into cosine similarity:

```sql
1 - (embedding <=> predicate_embedding)
```

The reviews are displayed in descending order of similarity.

### 7. Verify the Stored Embeddings

Connect to PostgreSQL:

```powershell
docker exec -it cmsc724-project-db psql -U postgres -d semantic_filter
```

Execute:

```sql
SELECT
    id,
    vector_dims(embedding) AS dimensions
FROM reviews
ORDER BY id;
```

All five sample reviews should have 384-dimensional embeddings.

Exit PostgreSQL using:

```text
\q
```

## Preliminary Similarity Results

Predicate: **The reviewer enjoyed the movie**

| Review ID | Review | Similarity |
|---|---|---:|
| 5 | The movie was boring and I almost fell asleep. | 0.5217 |
| 1 | I absolutely loved this movie. The acting was amazing. | 0.4853 |
| 4 | I would definitely recommend this movie to my friends. | 0.4835 |
| 3 | The story was interesting but the ending was disappointing. | 0.4830 |
| 2 | This was the worst movie I have ever watched. | 0.3952 |

These are preliminary measurements from five sample reviews, not classification accuracy results.

An important observation is that review 5, which expresses a negative opinion, received the highest similarity score.

This suggests that semantic similarity alone is not sufficient to determine whether a review satisfies a natural-language predicate.

Further evaluation using labeled examples and calibrated thresholds will be needed before Tier 1 can confidently accept or reject reviews.

## Remaining Work

- Implement similarity-based classification with calibrated thresholds.
- Implement the lightweight LLM classifier using Ollama.
- Combine embeddings and the small LLM into a two-tier cascade.
- Integrate semantic filtering into a PostgreSQL function using PL/Python.
- Add the large LLM tier.
- Implement caching and batching.
- Evaluate classification accuracy, execution time, model calls, and inference cost.
- Investigate PostgreSQL query planning and predicate ordering.
- Run ablation experiments to evaluate the contribution of each tier.

## Current Status

The first stage of the project is operational: PostgreSQL stores review embeddings and supports semantic similarity queries.

The complete `sem_filter()` operator and LLM cascade are still under development.

Our next milestone is to implement the small-LLM classification tier and evaluate how it can complement embedding-based similarity scoring.
