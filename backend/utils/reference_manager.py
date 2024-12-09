from typing import List, Dict, Optional, Tuple
import logging
import os
import json
import re
from config import settings
from urllib.parse import quote, urljoin
import asyncio
from bs4 import BeautifulSoup
import aiohttp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReferenceManager:
    def __init__(self):
        """Initialize the reference manager."""
        self.processed_refs: Dict[str, Dict] = {}  # ID -> metadata
        self.pending_refs: List[Dict] = []  # References to be processed
        self.failed_refs: List[Dict] = []  # References that failed to process
        
        # Create references directory if it doesn't exist
        self.refs_dir = os.path.join(settings.metadata_dir_path, "references")
        os.makedirs(self.refs_dir, exist_ok=True)
        
        # API settings
        self.s2_api_url = "https://api.semanticscholar.org/v1"
        self.s2_search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.arxiv_api_url = "http://export.arxiv.org/api/query"
        
        # Initialize aiohttp session
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def _fetch_with_redirect(self, session: aiohttp.ClientSession, url: str, headers: Dict = None) -> Tuple[int, Optional[bytes]]:
        """Fetch URL with redirect handling."""
        try:
            async with session.get(url, headers=headers, allow_redirects=True) as response:
                if response.status == 200:
                    return 200, await response.read()
                return response.status, None
        except Exception as e:
            logger.debug(f"Error fetching {url}: {str(e)}")
            return 0, None

    async def _try_arxiv_search(self, title: str) -> Optional[Dict]:
        """Search paper on arXiv."""
        try:
            query = quote(f'ti:"{title}"')
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.arxiv_api_url}?search_query={query}&max_results=1") as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'xml')
                        entry = soup.find('entry')
                        if entry:
                            pdf_url = entry.find('link', {'title': 'pdf'})
                            if pdf_url:
                                return {
                                    'title': entry.title.text,
                                    'pdf_url': pdf_url['href'],
                                    'source': 'arxiv'
                                }
        except Exception as e:
            logger.debug(f"arXiv search failed for {title}: {str(e)}")
        return None

    async def _try_google_scholar(self, title: str) -> Optional[str]:
        """Try to find PDF through Google Scholar."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            query = quote(f"{title} filetype:pdf")
            url = f"https://scholar.google.com/scholar?q={query}"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'html.parser')
                        for link in soup.find_all('a'):
                            href = link.get('href', '')
                            if href.lower().endswith('.pdf'):
                                return href
        except Exception as e:
            logger.debug(f"Google Scholar search failed for {title}: {str(e)}")
        return None

    async def fetch_paper_pdf(self, paper_data: Dict) -> Optional[bytes]:
        """Try to fetch PDF from various sources."""
        title = paper_data.get('title', '')
        if not title:
            return None

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # Try all potential sources in parallel
                tasks = []
                
                # 1. Try arXiv
                arxiv_data = await self._try_arxiv_search(title)
                if arxiv_data:
                    tasks.append(self._fetch_with_redirect(session, arxiv_data['pdf_url']))
                
                # 2. Try Semantic Scholar's PDF URL
                if paper_data.get('openAccessPdf', {}).get('url'):
                    tasks.append(self._fetch_with_redirect(session, paper_data['openAccessPdf']['url']))
                
                # 3. Try DOI resolution
                if paper_data.get('doi'):
                    doi_url = f"https://doi.org/{paper_data['doi']}"
                    tasks.append(self._fetch_with_redirect(session, doi_url))
                
                # 4. Try Google Scholar
                gs_url = await self._try_google_scholar(title)
                if gs_url:
                    tasks.append(self._fetch_with_redirect(session, gs_url))
                
                # 5. Try other URLs from paper metadata
                for url in paper_data.get('urls', []):
                    if url.lower().endswith('.pdf'):
                        tasks.append(self._fetch_with_redirect(session, url))
                
                # Try all sources
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, tuple):
                            status, content = result
                            if status == 200 and content:
                                return content
                
                logger.warning(f"No PDF found for paper: {title}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching PDF for {title}: {str(e)}")
            return None

    async def search_paper_by_title(self, title: str) -> Optional[Dict]:
        """Search for a paper using multiple sources."""
        try:
            # Try arXiv first
            arxiv_result = await self._try_arxiv_search(title)
            if arxiv_result:
                return arxiv_result

            # Try Semantic Scholar
            clean_title = quote(title)
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                # First try exact title
                async with session.get(
                    f"{self.s2_search_url}?query={clean_title}&limit=10",
                    headers={"Accept": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('data'):
                            # Find best match
                            best_match = None
                            highest_score = 0
                            
                            for paper in data['data']:
                                paper_title = paper.get('title', '')
                                if not paper_title:
                                    continue
                                
                                score = self._similarity_score(title, paper_title)
                                if score > highest_score and score > 0.5:
                                    highest_score = score
                                    best_match = paper
                            
                            if best_match:
                                # Get full details
                                paper_id = best_match['paperId']
                                async with session.get(
                                    f"{self.s2_api_url}/paper/{paper_id}",
                                    headers={"Accept": "application/json"}
                                ) as details_response:
                                    if details_response.status == 200:
                                        paper_data = await details_response.json()
                                        logger.info(f"Found paper: {paper_data.get('title')} (score: {highest_score:.2f})")
                                        return paper_data
            
            return None
                
        except Exception as e:
            logger.error(f"Error searching for paper {title}: {str(e)}")
            return None
    
    def _clean_title(self, title: str) -> str:
        """Clean title for search."""
        # Remove special characters but keep basic punctuation
        title = re.sub(r'[^\w\s\-:,]', '', title)
        # Normalize whitespace
        title = ' '.join(title.split())
        return title
    
    def _similarity_score(self, title1: str, title2: str) -> float:
        """Calculate similarity score between two titles using multiple metrics."""
        # Convert to lowercase
        t1 = title1.lower()
        t2 = title2.lower()
        
        # Direct match
        if t1 == t2:
            return 1.0
            
        # Word set similarity (Jaccard)
        words1 = set(t1.split())
        words2 = set(t2.split())
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard = intersection / union if union > 0 else 0
        
        # Calculate word sequence similarity
        # This helps with word order and partial matches
        seq_sim = 0
        for w1 in words1:
            if any(w1 in w2 or w2 in w1 for w2 in words2):
                seq_sim += 1
        seq_sim = seq_sim / max(len(words1), len(words2))
        
        # Combine scores (weighted average)
        return 0.6 * jaccard + 0.4 * seq_sim
    
    async def _try_unpaywall(self, doi: str) -> Optional[str]:
        """Try to get PDF URL from Unpaywall."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.unpaywall.org/v2/{doi}?email=refind@example.com"
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('is_oa') and data.get('best_oa_location', {}).get('url_for_pdf'):
                        return data['best_oa_location']['url_for_pdf']
        except Exception as e:
            logger.debug(f"Unpaywall lookup failed for DOI {doi}: {str(e)}")
        return None

    async def _try_core(self, title: str) -> Optional[str]:
        """Try to get PDF URL from CORE."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.core.ac.uk/v3/search/works",
                    params={
                        "q": title,
                        "limit": 1,
                        "filter": "downloadUrl:*"
                    },
                    headers={"Authorization": "Bearer rbAUfkIYPcGXJLhCBTEKsmM5u9zH0N2W"}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('results') and data['results'][0].get('downloadUrl'):
                        return data['results'][0]['downloadUrl']
        except Exception as e:
            logger.debug(f"CORE lookup failed for title {title}: {str(e)}")
        return None

    async def process_references(self, references: List[Dict]) -> Dict[str, str]:
        """Process a list of references and return their status."""
        status = {}
        
        for ref in references:
            ref_id = ref.get('title')  # Use title as ID
            if not ref_id:
                continue
                
            # Check if already processed
            if ref_id in self.processed_refs:
                status[ref_id] = "already_processed"
                continue
            
            # Try to fetch paper details
            paper_data = await self.search_paper_by_title(ref_id)
            if paper_data:
                # Try to fetch PDF
                pdf_content = await self.fetch_paper_pdf(paper_data)
                if pdf_content:
                    # Save PDF for processing
                    safe_filename = re.sub(r'[^\w\s-]', '_', ref_id)[:100]  # Limit filename length
                    pdf_path = os.path.join(settings.upload_dir_path, f"{safe_filename}.pdf")
                    try:
                        with open(pdf_path, 'wb') as f:
                            f.write(pdf_content)
                        
                        # Save metadata
                        self.save_reference_metadata(ref_id, paper_data)
                        status[ref_id] = "success"
                        self.pending_refs.append(ref)
                        logger.info(f"Successfully downloaded PDF for: {ref_id}")
                    except Exception as e:
                        logger.error(f"Error saving PDF for {ref_id}: {str(e)}")
                        status[ref_id] = "save_failed"
                        self.failed_refs.append(ref)
                else:
                    status[ref_id] = "pdf_not_found"
                    self.failed_refs.append(ref)
            else:
                status[ref_id] = "paper_not_found"
                self.failed_refs.append(ref)
        
        return status
    
    def save_reference_metadata(self, ref_id: str, metadata: Dict):
        """Save reference metadata to disk."""
        try:
            safe_filename = re.sub(r'[^\w\s-]', '_', ref_id)[:100]  # Limit filename length
            file_path = os.path.join(self.refs_dir, f"{safe_filename}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata for reference: {ref_id}")
        except Exception as e:
            logger.error(f"Error saving metadata for reference {ref_id}: {str(e)}")
    
    def load_reference_metadata(self, ref_id: str) -> Optional[Dict]:
        """Load reference metadata from disk."""
        try:
            safe_filename = re.sub(r'[^\w\s-]', '_', ref_id)[:100]  # Limit filename length
            file_path = os.path.join(self.refs_dir, f"{safe_filename}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading metadata for reference {ref_id}: {str(e)}")
            return None