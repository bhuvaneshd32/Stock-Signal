import faiss
import pickle
import numpy as np
import os
import logging
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self, index_dir="data/indices", model_name='all-MiniLM-L6-v2'):
        self.embedder = SentenceTransformer(model_name)
        
        # Load FAISS Index
        faiss_path = os.path.join(index_dir, "faiss.index")
        logger.info(f"Loading FAISS index from {faiss_path}")
        self.faiss_index = faiss.read_index(faiss_path)
        
        # Load BM25, Corpus, and Metadata
        meta_path = os.path.join(index_dir, "index_metadata.pkl")
        logger.info(f"Loading metadata from {meta_path}")
        with open(meta_path, 'rb') as f:
            data = pickle.load(f)
            self.bm25 = data['bm25']
            self.corpus = data['corpus']
            self.metadata = data['metadata']

    def search(self, query: str, top_k: int = 5, bm25_weight: float = 0.45, dense_weight: float = 0.55):
        logger.info(f"Executing hybrid search for: '{query}'")
        
        # --- 1. BM25 Lexical Scoring ---
        tokenized_query = query.lower().split()
        raw_bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores (Min-Max scaling to 0-1 range)
        max_bm25 = np.max(raw_bm25_scores) if np.max(raw_bm25_scores) > 0 else 1.0
        norm_bm25_scores = raw_bm25_scores / max_bm25

        # --- 2. FAISS Dense Scoring ---
        query_embedding = self.embedder.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)
        
        # We search the entire corpus to get distances for all chunks to combine with BM25
        distances, indices = self.faiss_index.search(query_embedding, len(self.corpus))
        
        # Reconstruct dense scores in the original corpus order
        # Since we used IndexFlatIP (Inner Product) with normalized vectors, distances are cosine similarities (-1 to 1)
        # We shift them to 0-1 range for easier weighting
        dense_scores = np.zeros(len(self.corpus))
        for idx, sim in zip(indices[0], distances[0]):
            dense_scores[idx] = (sim + 1) / 2 

        # --- 3. Hybrid Scoring ---
        hybrid_scores = (bm25_weight * norm_bm25_scores) + (dense_weight * dense_scores)
        
        # Get top K indices
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            results.append({
                "score": round(float(hybrid_scores[idx]), 4),
                "bm25_score": round(float(norm_bm25_scores[idx]), 4),
                "dense_score": round(float(dense_scores[idx]), 4),
                "text": self.corpus[idx],
                "metadata": self.metadata[idx]
            })
            
        return results

if __name__ == "__main__":
    retriever = HybridRetriever()
    
    # Let's test a realistic financial query
    test_query = "dividend declaration and record date"
    results = retriever.search(test_query, top_k=3)
    
    print(f"\n--- Top Results for: '{test_query}' ---")
    for i, res in enumerate(results, 1):
        print(f"\nResult {i} (Hybrid Score: {res['score']})")
        print(f"Date: {res['metadata']['Date']} | Category: {res['metadata']['Category']}")
        print(f"Headline: {res['metadata']['Headline']}")
        print(f"Text Snippet: {res['text'][:250]}...")
        print(f"Source: {res['metadata']['Link']}")