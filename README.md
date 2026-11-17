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
git clone https://github.com/YOUR_USERNAME/cmsc724-semantic-filtering.git
cd cmsc724-semantic-filtering
```

Replace `YOUR_USERNAME` with the repository owner's GitHub username.

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
- Local port: `5433`

The current configuration uses a simple password for local development only.

### 3. Initialize the Database

Run the following command from PowerShell:

```powershell
Get-Content sql/setup.sql | docker exec -i cmsc724-project-db psql -U postgres -d semantic_filter
```

Run this initialization once on a new database to create the table and insert the sample reviews.

### 4. Set Up the Python Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 5. Generate and Store Embeddings

```powershell
python src/embeddings.py
```

This script generates 384-dimensional embeddings for the stored reviews and saves them in PostgreSQL.

The embedding model will be downloaded automatically on first use.

### 6. Run a Similarity Search

```powershell
python src/similarity.py
```

The script compares each stored review against the predicate:

"The reviewer enjoyed the movie"

It displays the reviews ranked by cosine similarity.

### 7. Verify the Stored Embeddings

Connect to PostgreSQL:

```powershell
docker exec -it cmsc724-project-db psql -U postgres -d semantic_filter
```

Execute:

```sql
SELECT id, vector_dims(embedding)
FROM reviews;
```

All five sample reviews should have 384-dimensional embeddings.

Exit PostgreSQL using `\q`.

## Preliminary Similarity Results

Predicate: **The reviewer enjoyed the movie**

| Review ID | Similarity |
|---|---:|
| 5 | 0.5217 |
| 1 | 0.4853 |
| 4 | 0.4835 |
| 3 | 0.4830 |
| 2 | 0.3952 |

These are preliminary similarity measurements on five sample reviews, not classification accuracy results.

## Remaining Work

- Implement similarity-based classification with calibrated thresholds.
- Implement the lightweight LLM classifier.
- Combine embeddings and the small LLM into a two-tier cascade.
- Integrate semantic filtering into a PostgreSQL function using PL/Python.
- Add the large LLM tier.
- Implement caching and batching.
- Evaluate classification accuracy, execution time, model calls, and inference cost.
- Investigate PostgreSQL query planning and predicate ordering.

## Current Status

The first stage of the project is operational: PostgreSQL stores review embeddings and supports semantic similarity queries. The complete `sem_filter()` operator and LLM cascade are still under development.
