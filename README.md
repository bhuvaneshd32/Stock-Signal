# StockSignal: Evidence Retrieval Engine for Indian Equities

**StockSignal** is an evidence-first Information Retrieval (IR) engine built specifically for the Indian stock market. Instead of attempting speculative price predictions, StockSignal retrieves exact supporting passages from NSE and BSE corporate filings—such as Regulation 30 announcements, Management Discussion & Analysis (MD&A), Business Responsibility and Sustainability Reports (BRSR), and quarterly financial statements—alongside structured financial metrics.

---

## Architecture & Methodology

- **Data Ingestion**: Automates scraping and extraction of regulatory filings from Indian stock exchanges.
- **Hybrid Retrieval**: Combines lexical exact-word matching with dense semantic vector search.
  $$Score = 0.45 \times Score_{BM25} + 0.55 \times Score_{Dense}$$
  - **BM25**: Handles exact matches for scrip codes, technical terms, specific financial metrics, and proper nouns.
  - **Dense Vectors**: Encodes text chunks using `all-MiniLM-L6-v2` via FAISS to capture semantic intent and conceptual queries.
- **Evidence Citations**: Returns exact source documentation, corporate announcement dates, scrip metadata, and paragraph-level contexts.

---

## Repository Structure & File Summary

```text
stock-signal/
├── data/
│   ├── raw/                 # Stores raw downloaded PDFs, HTMLs, and JSON payloads from BSE/NSE
│   ├── processed/           # Stores cleaned, chunked text segments with structural metadata
│   └── indices/             # Stores serialized FAISS vector spaces and BM25 index artifacts
├── src/
│   ├── __init__.py          # Package initialization module
│   ├── ingestion/           # Scrapers and parsers for exchange disclosures
│   ├── indexer/             # Embedding generation and index creation pipelines
│   ├── retriever/           # Hybrid scoring engine and query routing logic
│   └── api/                 # FastAPI server definitions for frontend/client consumption
├── tests/                   # Automated validation and labeled IR evaluation suites
├── notebooks/               # Sandbox environments for prototyping and evaluation
├── .gitignore               # Excludes large binaries, virtual environments, and raw caches
├── requirements.txt         # Project dependency definitions
└── README.md                # Project documentation and setup guide
