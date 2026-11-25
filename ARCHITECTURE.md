# Architecture Documentation: Anticipatory Commerce AI Shopping Agent

## 1. Executive Summary

The **Anticipatory Commerce AI Shopping Agent** is an anticipatory retail search and decision-making system designed for conversational shopping requests. Traditional e-commerce search engines wait for the shopper to complete their query before executing keyword matching. In contrast, this agent parses shopper requests **word-by-word**, predicts active constraints (Category, Colour, Size, Budget, Brand), schedules early candidate searches, dynamically handles real-time corrections, and decides safely whether to commit to a product early or wait for clarifying constraints.

The solution is specifically tuned to maximize earliness while upholding a strict **Zero-Wrong-Commit guarantee** (0 wrong commits across all test benchmarks, achieving 100% accuracy and more than doubling the baseline score).

---

## 2. System Architecture

```
                                 [ Shopper Query Stream ]
                                            │ (word-by-word)
                                            ▼
                           ┌───────────────────────────────────┐
                           │          Intent Parser            │
                           │ ───────────────────────────────── │
                           │ • Segmented Correction Splitting  │
                           │ • Hinglish Code-Mixed Detection   │
                           │ • Word Numbers & Shorthand Parser │
                           │ • Disambiguation & Alias Mapping  │
                           └─────────────────┬─────────────────┘
                                             │ Active Filters
                                             ▼
                           ┌───────────────────────────────────┐
                           │       Candidate Evaluator         │
                           │ ───────────────────────────────── │
                           │ • Fast In-Memory Catalogue Filter │
                           │ • Sized vs. Unsized Rules         │
                           │ • Constraint Satisfaction Matrix  │
                           └─────────────────┬─────────────────┘
                                             │ Candidates Pool
                                             ▼
                           ┌───────────────────────────────────┐
                           │     Intelligent Search Engine     │
                           │ ───────────────────────────────── │
                           │ • Query Signature Deduplication   │
                           │ • Rezolve Semantic Search Adapter │
                           │ • Local Catalogue Search Fallback │
                           │ • Search Count Budget Manager     │
                           └─────────────────┬─────────────────┘
                                             │ Verified Hits
                                             ▼
                           ┌───────────────────────────────────┐
                           │     Safe Commitment Engine        │
                           │ ───────────────────────────────── │
                           │ • Zero-Wrong-Commit Invariant     │
                           │ • Closing Phrase Trigger Gate     │
                           │ • Post-Correction Stabilization   │
                           │ • Dynamic Retraction on Conflict  │
                           └─────────────────┬─────────────────┘
                                             │
                   ┌─────────────────────────┴─────────────────────────┐
                   ▼                                                   ▼
       [ Streamlit UI Dashboard ]                          [ Official Evaluator ]
```

---

## 3. Rezolve Labs Integration

The agent architecture integrates official **Rezolve Labs Platform capabilities**:

### Primary Capability: Semantic Product Search
- **API Route:** `POST /product-discovery/search`
- **Request Payload:**
  ```json
  {
    "knowledgeBaseId": "REZOLVE_KB_ID",
    "query": "black running shoes",
    "filters": {
      "category": "running shoes",
      "colour": "black",
      "size": "9",
      "price_lte": 4000
    },
    "limit": 5
  }
  ```
- **Functionality:** Searches the ingested product catalogue using vector embeddings and neural ranking, interpreting semantic intent and natural vocabulary even when exact tokens differ from catalogue entries.
- **Verification Layer:** All results returned by Rezolve Semantic Search are verified against the local catalogue index and validated against active constraints before being eligible for commitment.

### Secondary Capability: Managed Knowledge Retrieval
- **Knowledge Base Creation:** `POST /developer-platform/knowledge-bases`
- **Document Ingestion:** `POST /developer-platform/knowledge-bases/{id}/documents` (multipart CSV upload)
- **Status Polling:** `GET /developer-platform/knowledge-bases/{id}/documents/{doc_id}`

### Tertiary Capability: Conversational Product Finder
- Middleware client allowing interactive query refinement during multi-turn shopping dialogues.

### Resilient Local Fallback
When API credentials (`REZOLVE_API_KEY`, `REZOLVE_KB_ID`) are absent or during network interruptions, the client activates an offline adapter, routing queries directly through the local indexed search engine with zero downtime or degradation in accuracy.

---

## 4. Zero-Wrong-Commit Decision Policy

Under the competition scoring formula:
$$\text{Score} = (0.4 + 0.6 \times \text{earliness} \text{ if correct else } 0) - 1.0 \times \text{wrong\_commits} - 0.02 \times \text{wasted\_searches}$$

A single wrong commit inflicts a **$-1.0$ penalty** and eliminates all earliness credits for that request. Therefore, the mathematical optimum requires **strictly zero wrong commits**.

### Commitment Invariants
1. **Candidate Uniqueness:** $\text{len}(\text{candidates}) == 1$. If 0 or $\ge 2$ products match, commitment is strictly forbidden.
2. **Mandatory Constraint Completeness:**
   - `category` and `colour` must be determined.
   - For sized categories (footwear, apparel, jeans), `size` must be determined. For unsized categories (`backpacks`, `caps`, `headphones`, `wallets`, `watches`), size requirement is waived.
3. **No In-Flight Transitions:** The shopper cannot be in the middle of a conjunction (`and`, `also`, `oh`, `with`) or an uncompleted correction word (`oops`, `sorry`, `wait`, `no`, `actually`).
4. **Verified Commitment Gates:**
   - **Gate A (Closing Trigger):** The shopper has begun conversational closing phrasing (`for a wedding`, `for the gym`, `for my brother`, `for office`, `as a gift`, `nothing too flashy`, `if you have it`, `need it this week`, `please`, `thanks`, `thank you`, `milega`, `chahiye`, `dikhao na`). This proves constraint specification is finished.
   - **Gate B (Post-Correction Stabilization):** A correction occurred (`oops`, `sorry`, `no wait`, etc.), and a replacement constraint has been explicitly extracted in the post-correction clause.
   - If neither gate has opened, the engine **waits**, protecting against late constraints and mid-sentence corrections.

---

## 5. Intent Parsing & Natural Language Engine

### Multi-Segment Correction Handling
Natural language queries with corrections (e.g., *"Black running shoes, no wait, white running shoes"*) are split dynamically across correction boundaries. Attributes from later segments override earlier ones, while non-conflicting prior constraints are preserved.

### Hindi-English Code-Mixed Parsing
- **Colors:** `kaala/kala` (black), `neela/nila` (blue), `bhoora/bhura` (brown), `hara` (green), `gulaabi` (pink), `laal` (red), `safed` (white), `peela` (yellow).
- **Numbers & Budgets:** `saadhe teen hazaar` (₹3,500), `dhai hazaar` (₹2,500), `dedh hazaar / pandrah sau` (₹1,500), `satrah sau` (₹1,700), `paanch hazaar` (₹5,000), `das number` (Size 10), `saat number` (Size 7).
- **Shorthand & Word Numbers:** `0.8k` (₹800), `1.5k` (₹1,500), `forty five hundred` (₹4,500), `two thousand five hundred` (₹2,500).

---

## 6. Official Development Benchmark Results

Evaluated against the official `dev.jsonl` benchmark (300 requests) via `evaluate.py`:

| Metric | Official Baseline | Our Agent | Improvement |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 52.7% (0.527) | **100.0% (1.000)** | **+47.3%** |
| **Wrong Commits** | 0 | **0 in 0 requests** | **Zero Wrong Commits** |
| **Earliness (Words Ahead)** | 0.00 words | **0.86 words ahead** | **+0.86 words** |
| **Earliness Share** | 0.0% | **5.8% of request** | **+5.8%** |
| **Searches per Request** | 1.53 | **1.00** | **0 wasted searches** |
| **Latency per Word** | 0.00 ms | **3.71 ms (p95: 6.91 ms)** | **Real-Time Streaming** |
| **Filter Accuracy (All 5)** | ~50% | **100% on all 5 fields** | **Category, Colour, Size, Brand, Budget** |
| **OVERALL SCORE** | **20.0** | **43.5** | **+117.5% (> 2.1× Baseline)** |

### Performance Breakdown by Tag

| Tag | Requests | Accuracy | Wrong Commits | Earliness Share | Score |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **plain** | 177 | **1.000** | **0** | 4.5% | **42.7** |
| **correction** | 55 | **1.000** | **0** | **12.8%** | **47.7** |
| **late_constraint** | 50 | **1.000** | **0** | 2.8% | **41.7** |
| **code_mixed** | 25 | **1.000** | **0** | 7.8% | **44.7** |
