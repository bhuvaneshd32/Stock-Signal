# Stock-Signal


# File Structure
stock-signal/
├── data/
│   ├── raw/                 # Downloaded PDFs, JSONs from BSE/NSE
│   ├── processed/           # Cleaned, chunked text passages with metadata
│   └── indices/             # Serialized FAISS & BM25 index artifacts
├── src/
│   ├── __init__.py
│   ├── ingestion/           # BSE/NSE scrapers and PDF parsers
│   ├── indexer/             # Embedding generation & FAISS/BM25 builder
│   ├── retriever/           # Hybrid search engine & ranker
│   └── api/                 # FastAPI endpoints for search & metadata
├── tests/                   # Labeled IR evaluation test suite
├── notebooks/               # Exploration & evaluation notebooks
├── .gitignore
├── requirements.txt
└── README.md
