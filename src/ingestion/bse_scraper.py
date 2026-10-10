from curl_cffi import requests
import pandas as pd
from typing import Optional, List, Dict
import logging
import os
from datetime import datetime, timedelta  # <-- ADD THIS IMPORT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BSEScraper:
    def __init__(self):
        self.base_url = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
        
        # Initialize a persistent session that impersonates Chrome
        self.session = requests.Session(impersonate="chrome")
        
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.bseindia.com",
            "Referer": "https://www.bseindia.com/",
        })

        # Step 1: Visit the homepage to acquire security cookies
        try:
            logger.info("Initializing session and fetching cookies from BSE homepage...")
            self.session.get("https://www.bseindia.com/", timeout=15)
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")

    def fetch_announcements(self, scrip_code: int, page_no: int = 1) -> pd.DataFrame:
        # Calculate a 1-year date window
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        params = {
            "pageno": str(page_no),
            "strCat": "-1",
            "strPrevDate": start_date.strftime("%Y%m%d"),  # From Date (YYYYMMDD)
            "strScrip": str(scrip_code),
            "strSearch": "P",
            "strToDate": end_date.strftime("%Y%m%d"),    # To Date (YYYYMMDD)
            "strType": "C"
        }
        
        try:
            logger.info(f"Fetching page {page_no} for scrip {scrip_code} (from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})...")
            response = self.session.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 403:
                logger.error("403 Forbidden: The BSE API blocked the request.")
                return pd.DataFrame()
                
            data = response.json()
            
            if "Table" in data and data["Table"]:
                return self._parse_announcements(data["Table"])
            else:
                logger.warning(f"No data found for scrip {scrip_code} on page {page_no}.")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Failed to fetch data for scrip {scrip_code}: {e}")
            return pd.DataFrame()
        
    def _parse_announcements(self, raw_data: List[Dict]) -> pd.DataFrame:
        announcements = []
        for item in raw_data:
            link = None
            if item.get('ATTACHMENTNAME'):
                link = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{item.get('ATTACHMENTNAME')}"
                
            announcements.append({
                "Scrip_Code": item.get("SCRIP_CD"),
                "Company_Name": item.get("SLONGNAME"),
                "Date": item.get("NEWS_DT"),
                "Category": item.get("CATEGORYNAME"),
                "Headline": item.get("HEADLINE"),
                "Text": item.get("MORE"),
                "Attachment_Link": link
            })
            
        df = pd.DataFrame(announcements)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df

if __name__ == "__main__":
    scraper = BSEScraper()
    tcs_df = scraper.fetch_announcements(scrip_code=532540, page_no=1)
    
    if not tcs_df.empty:
        print("\nSuccessfully fetched latest TCS announcements:")
        print(tcs_df[['Date', 'Headline', 'Category']].head(3))
        
        output_path = "data/raw/532540_announcements.csv"
        os.makedirs("data/raw", exist_ok=True)
        tcs_df.to_csv(output_path, index=False)
        print(f"\nSaved raw output to {output_path}")