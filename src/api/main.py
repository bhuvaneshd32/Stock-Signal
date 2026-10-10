from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv # ADD THIS

load_dotenv()

from src.retriever.search_engine import HybridRetriever
from src.ingestion.bse_scraper import BSEScraper
from src.ingestion.pdf_parser import FilingParser
from src.indexer.build_index import HybridIndexer

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    llm_model = genai.GenerativeModel('gemini-flash-latest')
else:
    logger.warning("GEMINI_API_KEY not found. AI Summaries will be disabled.")
    llm_model = None

app = FastAPI(
    title="StockSignal API",
    description="Evidence retrieval engine for Indian Equities",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = HybridRetriever(index_dir="data/indices")

class SearchResponse(BaseModel):
    query: str
    summary: Optional[str] = None
    results: List[Dict[str, Any]]

def run_ingestion_pipeline():
    try:
        logger.info("Starting background ingestion pipeline...")
        scraper = BSEScraper()
        target_scrips = {532540: "TCS", 500325: "Reliance", 532215: "Axis_Bank", 500180: "HDFC_Bank", 500209: "Infosys"}
        import pandas as pd
        all_announcements = []
        for scrip, name in target_scrips.items():
            df = scraper.fetch_announcements(scrip_code=scrip, page_no=1)
            if not df.empty:
                all_announcements.append(df)
                
        if all_announcements:
            raw_path = "data/raw/nifty50_announcements.csv"
            pd.concat(all_announcements, ignore_index=True).to_csv(raw_path, index=False)
            
            parser = FilingParser()
            parsed_path = "data/processed/nifty50_announcements_parsed.csv"
            parser.process_announcements(raw_path, parsed_path)
            
            indexer = HybridIndexer()
            indexer.build_indices(parsed_path)
            indexer.save_indices("data/indices")
            
            global retriever
            retriever = HybridRetriever(index_dir="data/indices")
            logger.info("Pipeline complete. Retriever reloaded with new data.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")

@app.get("/")
def read_root():
    return {"status": "StockSignal API is running. Use /search for queries."}

@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., description="The natural language search query"),
    top_k: int = Query(5, description="Number of results to return"),
    bm25_weight: float = Query(0.45, description="Weight for lexical search"),
    dense_weight: float = Query(0.55, description="Weight for dense vector search")
):
    raw_results = retriever.search(query=q, top_k=top_k, bm25_weight=bm25_weight, dense_weight=dense_weight)
    
    summary = None
    if llm_model and raw_results:
        # Construct the context payload from retrieved chunks
        context = "\n\n".join([f"Source [{i+1}]: {res['text']}" for i, res in enumerate(raw_results)])
        prompt = f"""You are a professional financial analyst. Based ONLY on the following extracted context from corporate filings, provide a concise, executive summary answering the user's query. 
        Cite your sources using [Source X]. If the answer is not fully available in the context, state that clearly. Do not hallucinate external information.
        
        Query: {q}
        
        Context:
        {context}
        """
        try:
            response = llm_model.generate_content(prompt)
            summary = response.text
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            summary = "AI summary generation failed."

    return {"query": q, "summary": summary, "results": raw_results}

@app.post("/update")
def trigger_update(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingestion_pipeline)
    return {"message": "Data update started in the background. This may take a few minutes."}

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)