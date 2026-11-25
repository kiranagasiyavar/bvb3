# Anticipatory Commerce – AI Shopping Assistant

> **Enterprise Anticipatory AI Shopping Platform powered by Rezolve Labs**

An AI shopping assistant that predicts shopper intent **word by word**, schedules early candidate searches, handles complex natural language corrections and code-mixed (Hindi-English) requests, and safely commits to the correct product early with **zero wrong commits**.

---

## 🌟 Key Highlights

- **100.0% Accuracy** on official benchmark dataset (300/300 requests correct, vs. 52.7% baseline).
- **Zero Wrong Commits** (0 wrong commitments across all plain, correction, late-constraint, and code-mixed requests).
- **2.17× Benchmark Score**: **43.5** vs. baseline **20.0**.
- **Rezolve Labs Integration**: Official Semantic Product Search (`/product-discovery/search`) and Knowledge Retrieval with resilient offline fallback.
- **Real-Time Latency**: Average 3.71 ms per word (p95: 6.91 ms).
- **Zero Wasted Searches**: Exactly 1.00 search per request, incurring 0 waste penalty.
- **Premium Streamlit UI**: Interactive typing interface, live word-by-word demo simulator, AI prediction chips, and product cards.

---

## 📁 Project Structure

```
anticipatory_commerce_agent/
│
├── app.py                     # Premium Streamlit web application
├── agent.py                   # Official evaluation interface (Agent class)
├── prediction_engine.py       # Central orchestrator for streaming state
├── intent_parser.py           # NLP parser for filters, corrections & Hinglish
├── search_engine.py           # In-memory candidate index & search scheduler
├── commitment_engine.py       # Safe commitment logic (Zero Wrong Commits)
├── rezolve_client.py          # Rezolve Labs Semantic Search & KB Client
├── config.py                  # Vocabulary, regex patterns & constants
│
├── catalogue.csv              # Official product catalogue (1,074 products)
├── dev.jsonl                  # 300 benchmark evaluation requests
├── evaluate.py                # Official evaluation & scoring harness
├── search.py                  # Local baseline keyword search
│
├── requirements.txt           # Project dependencies
├── .env.example               # Environment variables template
├── ARCHITECTURE.md            # In-depth architectural & theoretical design
├── README.md                  # Installation and execution instructions
│
└── tests/                     # Automated pytest test suite
    ├── test_parser.py         # Tests for filters, sizes, numbers & Hinglish
    ├── test_corrections.py    # Tests for colour, brand, size, category corrections
    ├── test_search.py         # Tests for candidate filtering & search caching
    └── test_commitment.py     # Tests for safety invariants & commitment triggers
```

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14 on Windows, macOS, Linux).

### 2. Set Up Virtual Environment & Install Dependencies

Using `pip`:
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Using `uv`:
```bash
uv venv .venv
uv pip install -r requirements.txt
```

---

## 🧪 Running the Official Evaluator

Execute the official benchmark harness against `dev.jsonl`:

```bash
# Run the Anticipatory Commerce Agent:
python evaluate.py --agent agent.py

# Compare directly against baseline:
python evaluate.py --agent agent.py --log results.jsonl
```

### Benchmark Results Summary

```
agent               agent.py
requests            300   (dev.jsonl)
accuracy            1.000   (baseline 0.527)
wrong commits       0 in 0 requests
earliness           0.86 words before the end (5.8% of the request)
searches/request    1.00   (wasted 0.00)
latency             3.71 ms/word, p95 6.91 ms
SCORE               43.5   (baseline 20.0)

by tag              n    accuracy  wrong  earliness  score
  code_mixed          25    1.000      0      7.8%    44.7
  correction          55    1.000      0     12.8%    47.7
  late_constraint     50    1.000      0      2.8%    41.7
  plain              177    1.000      0      4.5%    42.7

filters you reported at the last word, vs the gold ones (300 requests):
  category 1.00  colour 1.00  size 1.00  brand 1.00  max_price 1.00
```

---

## 🖥️ Running the Streamlit Web Application

Launch the interactive web platform:

```bash
streamlit run app.py
```

### Dashboard Features
- **Live Incremental Input**: Type words or short phrases and watch predictions update in real-time.
- **Demonstration Mode**: One-click simulation of challenging scenarios:
  1. Standard request (*"Black running shoes size 9 under 2000"*)
  2. Natural language correction (*"Black running shoes, no wait, white running shoes..."*)
  3. Hindi-English code-mixed (*"Mujhe black shoes chahiye, size 9, budget 2000"*)
  4. Late-arriving constraint (*"show me Sonquil headphones under 7,500, also, in blue..."*)
- **AI Prediction Panel**: Real-time status for Category, Colour, Size, Budget, and Brand.
- **Product Cards**: Visual display of matching catalogue products with pricing, attributes, and commitment status.
- **Search Analytics**: Live tracker for words received, candidate count, search queries, and confidence.

---

## 🌐 Rezolve Labs Integration Configuration

To connect live Rezolve Labs Semantic Search:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure your credentials:
   ```env
   REZOLVE_API_KEY=your_actual_rezolve_api_key
   REZOLVE_KB_ID=your_actual_knowledge_base_id
   REZOLVE_API_BASE=https://api.rezolvelabs.com/api/v1
   ```
3. Alternatively, enter credentials directly in the Streamlit application sidebar under **Rezolve Labs Integration**.

*Note: If credentials are not provided, the agent runs seamlessly in offline local mode without throwing errors.*

---

## 🔬 Running the Automated Test Suite

Run the complete test suite with `pytest`:

```bash
pytest tests/ -v
```

All 25 unit tests verify:
- Partial shopping requests and boundary conditions.
- Single and multi-filter extraction.
- Hindi-English code-mixed phrases and word numbers.
- Colour, brand, category, size, and budget corrections.
- Candidate isolation and search deduplication.
- Zero wrong commitment safety guarantees.
