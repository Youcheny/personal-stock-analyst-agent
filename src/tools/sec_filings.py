import requests
from .utils import rate_limited
import re
from bs4 import BeautifulSoup
import html
from typing import List, Dict, Optional

SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_TICKER_CIK = "https://www.sec.gov/files/company_tickers.json"
SEC_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

class SecFilings:
    def __init__(self, user_agent: str):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _get(self, url: str):
        r = self.session.get(url, timeout=15)
        r.raise_for_status()
        return r

    @rate_limited(4)
    def ticker_to_cik(self, ticker: str) -> Optional[str]:
        try:
            data = self._get(SEC_TICKER_CIK).json()
            for _, row in data.items() if isinstance(data, dict) else enumerate(data):
                t = (row.get("ticker") or "").upper()
                if t == ticker.upper():
                    return str(row.get("cik_str")).zfill(10)
        except Exception:
            return None

    @rate_limited(4)
    def latest_filings(self, ticker: str, forms, limit: int = 3):
        cik = self.ticker_to_cik(ticker)
        if not cik:
            return []
        try:
            url = SEC_SUBMISSIONS.format(cik=cik)
            js = self._get(url).json()
            recent = js.get("filings", {}).get("recent", {})
            form_list = recent.get("form", [])
            accnos = recent.get("accessionNumber", [])
            primdocs = recent.get("primaryDocument", [])
            dates = recent.get("filingDate", [])
            out = []
            for f, a, p, d in zip(form_list, accnos, primdocs, dates):
                if f in forms:
                    acc_nodashes = a.replace("-", "")
                    href = f"{SEC_ARCHIVES_BASE}/{int(cik)}/{acc_nodashes}/{p}"
                    out.append({"form": f, "date": d, "url": href})
                    if len(out) >= limit:
                        break
            return out
        except Exception:
            return []

    def extract_risk_items(self, filings: List[Dict]) -> List[str]:
        items = []
        for f in filings:
            try:
                response = self._get(f["url"])
                # Check if it's HTML content
                if "text/html" in response.headers.get("content-type", ""):
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    # Get text content
                    text = soup.get_text()
                else:
                    # For non-HTML content, try to extract text
                    text = response.text
                
                # Clean up the text
                text = self._clean_text(text)
                
                # Look for risk-related content
                risk_snippets = self._extract_risk_snippets(text)
                items.extend(risk_snippets)
                
            except Exception as e:
                continue
        
        # Remove duplicates and clean up
        seen = set()
        cleaned = []
        for item in items:
            if item and len(item) > 20 and item not in seen:  # Ensure meaningful content
                cleaned.append(item)
                seen.add(item)
        
        return cleaned[:8]

    def _clean_text(self, text: str) -> str:
        """Clean up text by removing excessive whitespace and special characters."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove common HTML entities
        text = html.unescape(text)
        # Remove XBRL-like tags
        text = re.sub(r'<[^>]*>', '', text)
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', '', text)
        return text.strip()

    def _extract_risk_snippets(self, text: str) -> List[str]:
        """Extract meaningful risk-related snippets from text."""
        snippets = []
        
        # Split into sentences and look for risk-related content
        sentences = re.split(r'[.!?]+', text)
        
        risk_keywords = [
            'risk', 'risks', 'uncertainty', 'uncertainties', 'challenge', 'challenges',
            'threat', 'threats', 'vulnerability', 'vulnerabilities', 'exposure',
            'volatility', 'volatile', 'fluctuation', 'fluctuations'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30:  # Skip very short sentences
                continue
                
            # Check if sentence contains risk-related keywords
            if any(keyword in sentence.lower() for keyword in risk_keywords):
                # Clean up the sentence
                clean_sentence = self._clean_text(sentence)
                if len(clean_sentence) > 30 and len(clean_sentence) < 300:
                    snippets.append(clean_sentence)
        
        return snippets
