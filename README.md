# LLM Cascade-Based Semantic Filtering in PostgreSQL

CMSC724 – Database Management Systems

## Project Overview

This project investigates semantic filtering over text stored in PostgreSQL through a proposed three-tier architecture. Given a review and a natural-language predicate, the eventual `sem_filter()` operator should return whether the review satisfies that predicate.

The proposed tiers are:

1. **Tier 1 — Embeddings + pgvector:** Compute cosine similarity, then use calibrated thresholds to accept or reject sufficiently clear cases.
2. **Tier 2 — Small LLM:** Use Llama 3.2 (3B) through Ollama to classify cases not resolved by Tier 1.
3. **Tier 3 — Larger LLM:** Use Llama 3 (8B) through Ollama for cases escalated from Tier 2.

Future work includes confidence calibration, batching, caching, PostgreSQL PL/Python integration, and query-planner experiments.

## Current Implementation (Intermediate Checkpoint)

The repository currently includes:

- PostgreSQL 17 in Docker with the pgvector extension and five sample movie reviews.
- 384-dimensional review embeddings generated using `all-MiniLM-L6-v2` and stored with pgvector.
- Cosine similarity queries using PostgreSQL's `<=>` operator.
- A small-LLM Boolean classifier (`llama3.2:3b`).
- A larger-LLM Boolean classifier (`llama3:latest`).
- A Python integration pipeline that computes similarity, calls Tier 2, and **diagnostically** escalates review ID 4 to Tier 3.
- CSV exports recording similarity scores, classifications, routing decisions, and measured request times.

**Current limitations:** Tier 1 thresholds have not been calibrated, so Tier 1 makes **no final classifications** and all five reviews proceed to Tier 2. Review ID 4 is escalated using a hardcoded diagnostic rule, **not** model confidence. The prototype runs as Python scripts; it is **not yet** a PostgreSQL PL/Python `sem_filter()` function. We have not demonstrated lower inference costs or improved classification accuracy.

## Repository Structure

```text
cmsc724-semfiltering/
├── README.md
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── sql/
│   └── setup.sql
├── src/
│   ├── embeddings.py
│   ├── similarity.py
│   ├── classifier.py
│   ├── compare_models.py
│   └── cascade.py
└── experiments/
    ├── cascade_results.csv
    ├── cascade_results_run1.csv
    ├── cascade_results_run2.csv
    ├── model_comparison.csv
    └── cascade_three_tier_results.csv
```

## Prerequisites

- Docker Desktop (with the Docker engine running)
- Python (developed using Python 3.13)
- Git
- Ollama (with its local service running)

The commands below use **Windows PowerShell**. PostgreSQL runs in Docker, while the Ollama service runs separately on the host computer.

## Setup Instructions

### 1. Clone the repository

```powershell
git clone https://github.com/npraharsh/cmsc724-semfiltering.git
cd cmsc724-semfiltering
```

### 2. Start PostgreSQL

Make sure Docker Desktop is open and the engine is running.

```powershell
docker compose up -d
docker ps
```

The Compose configuration starts the following local development database:

- Container: `cmsc724-project-db`
- Database: `semantic_filter`
- Username: `postgres`
- Password: `postgres`
- Host port: `5433` (bound to `127.0.0.1`)

The password is **only for local development**. Do not expose this database publicly or use these credentials for deployment. The named Docker volume preserves PostgreSQL data across container restarts.

### 3. Initialize the database

From the repository root, run:

```powershell
Get-Content sql/setup.sql | docker exec -i cmsc724-project-db psql -v ON_ERROR_STOP=1 -U postgres -d semantic_filter
```

This enables pgvector, creates the `reviews` table, and inserts five sample reviews if their text is not already present. The initialization is designed to avoid duplicating those example texts on normal sequential reruns.

### 4. Set up Python dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 5. Generate and verify embeddings

```powershell
python src/embeddings.py
```

The first run downloads `all-MiniLM-L6-v2` if necessary. Check that each review has a 384-dimensional embedding:

```powershell
docker exec cmsc724-project-db psql -U postgres -d semantic_filter -c "SELECT id, vector_dims(embedding) AS dimensions FROM reviews ORDER BY id;"
```

### 6. Run the Tier 1 similarity search

```powershell
python src/similarity.py
```

The script ranks the reviews against the predicate **“The reviewer enjoyed the movie.”** Similarity is calculated as `1 - cosine_distance`, using pgvector's `<=>` operator. **A high similarity score does not necessarily mean the review satisfies the predicate.**

### 7. Install and test the Ollama models

Install and launch Ollama, then run:

```powershell
ollama pull llama3.2:3b
ollama pull llama3:latest
ollama list
```

Keep the Ollama service running. The Python classifier sends requests to `http://localhost:11434/api/generate`. The first request to a model may include significant model-loading overhead.

### 8. Run the small-LLM classifier (Tier 2)

```powershell
python src/classifier.py
```

This retrieves reviews from PostgreSQL, classifies them with Llama 3.2 (3B), and displays Boolean predictions and request times.

### 9. Compare the small and larger models

```powershell
python src/compare_models.py
```

This runs both Llama 3.2 (3B) and Llama 3 (8B) on the same five reviews and saves predictions and timing data to `experiments/model_comparison.csv`.

**Note:** Re-running this script overwrites that CSV. Copy the file first if you want to preserve a previous run.

### 10. Run the integrated three-tier diagnostic pipeline

```powershell
python src/cascade.py
```

The current pipeline performs the following steps:

1. Generate an embedding for the natural-language predicate.
2. Use pgvector to compute a similarity score for each review.
3. Forward every review to the small LLM because Tier 1 thresholds are not calibrated.
4. Explicitly escalate review **ID 4** to the larger LLM as a diagnostic test of Tier 3 routing.
5. Use the Tier 3 result as the final classification for the escalated review and save the results to `experiments/cascade_three_tier_results.csv`.

**This is diagnostic routing, not confidence-based escalation.** The selected review ID assumes the original five-row dataset with the same IDs. Re-running the pipeline overwrites its output CSV.

## Preliminary Results

All measurements below come from a small five-review prototype, not a controlled or statistically meaningful evaluation.

### Tier 1: Similarity scores

Predicate: **“The reviewer enjoyed the movie.”**

| Review ID | Review description | Cosine similarity |
|---|---|---:|
| 1 | Absolutely loved movie | 0.4853 |
| 2 | Worst movie ever | 0.3952 |
| 3 | Interesting story, disappointing ending | 0.4830 |
| 4 | Would recommend movie | 0.4835 |
| 5 | Boring movie | 0.5217 |

The negative review (ID 5) received the highest similarity score. This example illustrates why embedding similarity should not be treated as an uncalibrated Boolean classification.

### Tier 2 vs. Tier 3: Independent model comparison

| Review ID | Llama 3.2 (3B) | Llama 3 (8B) |
|---|---|---|
| 1 | TRUE | TRUE |
| 2 | FALSE | FALSE |
| 3 | FALSE | FALSE |
| 4 | TRUE | FALSE |
| 5 | FALSE | FALSE |

The models agreed on **four of five** reviews. They disagreed on review 4, which says the reviewer would definitely recommend the movie. The disagreement is useful for qualitative analysis, but these examples are too few to establish general model accuracy.

| Metric from one comparison run | Llama 3.2 (3B) | Llama 3 (8B) |
|---|---:|---:|
| Total Ollama request time (five reviews) | 38.506 s | 123.140 s |
| Average request time excluding first call | 4.059 s | 7.662 s |

The first requests may include model-loading overhead. These figures are **preliminary observations**, not controlled latency benchmarks.

### Three-tier integration test

| Metric | Observed |
|---|---:|
| Reviews processed | 5 |
| Tier 1 final classifications | 0 |
| Tier 2 LLM calls | 5 |
| Tier 3 LLM calls | 1 |
| Total LLM calls | 6 |
| Tier 2 total request time | 54.732 s |
| Tier 3 total request time | 91.439 s |
| Total pipeline wall-clock time | 277.633 s |

Review 4 was escalated for testing and returned `FALSE` from Tier 3, whereas Tier 2 returned `TRUE`. This confirms that the escalation path functions; it **does not** establish an accuracy improvement. Total pipeline time includes Python startup, embedding-model setup, database work, and LLM calls. The difference between wall-clock and Ollama request time should not be attributed entirely to database overhead.

Additional experiment CSVs in `experiments/` record earlier Tier 1 → Tier 2 pipeline runs.

## Remaining Work

- Expand the evaluation set and establish predicate-specific ground-truth labels.
- Calibrate vector-similarity thresholds and implement reliable Tier 1 acceptance and rejection.
- Estimate small-LLM classification confidence and develop a confidence-based escalation policy.
- Expose a SQL-callable `sem_filter()` function using PostgreSQL PL/Python.
- Add batching and caching to reduce repeated LLM work.
- Study PostgreSQL query planning, function cost estimates, and predicate ordering.
- Run controlled ablations and measure precision, recall, F1, latency, LLM calls, and inference cost.

## Current Status

This repository contains an **intermediate research prototype** with functional embedding search, two LLM classifiers, and a diagnostic three-tier execution path. A fully calibrated, cost-saving PostgreSQL-native semantic filter remains future work.
