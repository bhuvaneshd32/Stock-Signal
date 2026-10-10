from curl_cffi import requests
import pandas as pd
import pypdf
import io
import os
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FilingParser:
    def __init__(self):
        # Use a session to impersonate Chrome for PDF downloads too
        self.session = requests.Session(impersonate="chrome")
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bseindia.com/corporates/ann.html",
            "Accept": "application/pdf, text/plain, */*"
        })

    def extract_text_from_pdf(self, url: str) -> str:
        if not isinstance(url, str) or not url.startswith('http'):
            return ""
            
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code != 200:
                logger.warning(f"Failed to download PDF (Status {response.status_code}): {url}")
                return ""

            pdf_file = io.BytesIO(response.content)
            reader = pypdf.PdfReader(pdf_file)
            
            text_blocks = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_blocks.append(text.strip())
                    
            full_text = "\n".join(text_blocks)
            return " ".join(full_text.split())
            
        except Exception as e:
            logger.error(f"Error parsing PDF at {url}: {e}")
            return ""

    def process_announcements(self, input_csv: str, output_csv: str):
        logger.info(f"Loading data from {input_csv}")
        df = pd.read_csv(input_csv)
        
        df_with_links = df.dropna(subset=['Attachment_Link']).copy()
        
        tqdm.pandas(desc="Downloading & Parsing PDFs")
        df_with_links['Extracted_Text'] = df_with_links['Attachment_Link'].progress_apply(self.extract_text_from_pdf)
        
        df['Extracted_Text'] = df['Attachment_Link'].map(
            df_with_links.set_index('Attachment_Link')['Extracted_Text']
        )
        
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved parsed data to {output_csv}")

if __name__ == "__main__":
    parser = FilingParser()
    input_path = "data/raw/532540_announcements.csv"
    output_path = "data/processed/532540_announcements_parsed.csv"
    
    if os.path.exists(input_path):
        parser.process_announcements(input_path, output_path)
    else:
        logger.error(f"Input file not found: {input_path}")