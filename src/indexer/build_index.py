import pandas as pd
import numpy as np
import faiss
import pickle
import os
import logging
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridIndexer:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        logger.info(f"Loading SentenceTransformer model: {model_name}")
        self.embedder = SentenceTransformer(model_name)
        self.bm25 = None
        self.faiss_index = None
        self.metadata = []
        self.corpus = []

    def _chunk_text(self, text, max_words=200):
        """Splits long PDF text into smaller, search-friendly chunks."""
        words = str(text).split()
        chunks = []
        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i:i + max_words])
            if len(chunk.split()) > 10:  # Ignore very small chunks
                chunks.append(chunk)
        return chunks

    def build_indices(self, input_csv: str):
        logger.info(f"Loading parsed data from {input_csv}")
        df = pd.read_csv(input_csv)
        
        # We only want rows that have text to search
        df = df.dropna(subset=['Extracted_Text', 'Headline']).copy()
        
        logger.info("Chunking documents...")
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Documents"):
            # We index both the headline and the extracted PDF text
            full_text = f"{row['Headline']} - {row['Extracted_Text']}"
            chunks = self._chunk_text(full_text)
            
            for chunk in chunks:
                self.corpus.append(chunk)
                self.metadata.append({
                    "Scrip_Code": row.get('Scrip_Code'),
                    "Company_Name": row.get('Company_Name'),
                    "Date": row.get('Date'),
                    "Category": row.get('Category'),
                    "Headline": row.get('Headline'),
                    "Link": row.get('Attachment_Link')
                })

        logger.info(f"Created {len(self.corpus)} text chunks for indexing.")

        # 1. Build BM25 Index (Lexical)
        logger.info("Building BM25 Lexical Index...")
        tokenized_corpus = [doc.lower().split() for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 2. Build FAISS Index (Semantic)
        logger.info("Building FAISS Dense Index...")
        embeddings = self.embedder.encode(self.corpus, show_progress_bar=True, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        
        # Normalize vectors for Cosine Similarity
        faiss.normalize_L2(embeddings)
        self.faiss_index = faiss.IndexFlatIP(dimension) # Inner Product is Cosine Sim when normalized
        self.faiss_index.add(embeddings)

    def save_indices(self, output_dir: str):
        os.makedirs(output_dir, exist_ok=True)
        
        # Save FAISS
        faiss_path = os.path.join(output_dir, "faiss.index")
        faiss.write_index(self.faiss_index, faiss_path)
        
        # Save BM25 and Metadata using Pickle
        meta_path = os.path.join(output_dir, "index_metadata.pkl")
        with open(meta_path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'corpus': self.corpus,
                'metadata': self.metadata
            }, f)
            
        logger.info(f"Successfully saved indices and metadata to {output_dir}/")

if __name__ == "__main__":
    indexer = HybridIndexer()
    input_path = "data/processed/532540_announcements_parsed.csv"
    output_dir = "data/indices"
    
    if os.path.exists(input_path):
        indexer.build_indices(input_path)
        indexer.save_indices(output_dir)
    else:
        logger.error(f"Input file not found: {input_path}")