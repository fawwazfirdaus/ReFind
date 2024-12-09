import httpx
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from config import settings

logger = logging.getLogger(__name__)

class GrobidClient:
    def __init__(self, base_url: str = settings.GROBID_URL):
        """Initialize the GROBID client."""
        self.base_url = base_url.rstrip('/')
        self.timeout = httpx.Timeout(60.0)  # 60 seconds timeout
    
    async def process_pdf(self, pdf_path: str) -> Optional[str]:
        """Process a PDF file and return TEI XML."""
        try:
            url = f"{self.base_url}/api/processFulltextDocument"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                with open(pdf_path, 'rb') as pdf_file:
                    files = {'input': pdf_file}
                    response = await client.post(url, files=files)
                
                if response.status_code == 200:
                    return response.text
                else:
                    logger.error(f"GROBID processing failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error processing PDF with GROBID: {str(e)}")
            return None
    
    async def extract_metadata(self, tei_content: str) -> Dict:
        """Extract metadata from TEI XML."""
        try:
            soup = BeautifulSoup(tei_content, 'xml')
            
            # Extract basic metadata
            metadata = {
                'title': self._extract_text(soup.find('title')),
                'abstract': self._extract_text(soup.find('abstract')),
                'authors': self._parse_authors(soup),
                'references': self._parse_references(soup)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {}
    
    async def extract_full_text(self, tei_content: str) -> Optional[str]:
        """Extract full text content from TEI XML."""
        try:
            soup = BeautifulSoup(tei_content, 'xml')
            text_parts = []
            
            # Get body text
            body = soup.find('body')
            if body:
                for div in body.find_all('div'):
                    # Get section title
                    head = div.find('head')
                    if head:
                        text_parts.append(f"\n## {self._extract_text(head)}\n")
                    
                    # Get paragraphs
                    for p in div.find_all('p'):
                        text_parts.append(self._extract_text(p))
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting full text: {str(e)}")
            return None
    
    def _extract_text(self, element) -> str:
        """Extract clean text from a BeautifulSoup element."""
        if not element:
            return ''
        return ' '.join(element.get_text().split())
    
    def _parse_authors(self, soup) -> List[Dict]:
        """Parse author information from the TEI XML."""
        authors = []
        try:
            # Find sourceDesc which contains the proper author list
            source_desc = soup.find('sourceDesc')
            if not source_desc:
                return authors

            # Find authors within sourceDesc
            for author in source_desc.find_all(['author', 'editor']):
                try:
                    # Must have persName to be considered an author
                    persname = author.find('persName')
                    if not persname:
                        continue

                    # Must have both forename and surname
                    forename = persname.find('forename')
                    surname = persname.find('surname')
                    if not forename or not surname:
                        continue

                    firstname = self._extract_text(forename)
                    lastname = self._extract_text(surname)
                    
                    # Skip if either name component is missing or looks like an organization
                    if not firstname or not lastname or len(firstname) < 2 or len(lastname) < 2:
                        continue
                    
                    # Get affiliation info
                    affiliation = None
                    affiliation_elem = author.find('affiliation')
                    if affiliation_elem:
                        org_name = affiliation_elem.find('orgName')
                        if org_name:
                            affiliation = self._extract_text(org_name)
                    
                    # Get email
                    email = self._extract_text(author.find('email'))
                    
                    # Get ORCID if available
                    idno = author.find('idno', type='ORCID')
                    orcid = self._extract_text(idno) if idno else None

                    author_data = {
                        "firstname": firstname,
                        "lastname": lastname,
                        "email": email if email else None,
                        "affiliation": affiliation,
                        "orcid": orcid
                    }
                    authors.append(author_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing individual author: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"Error parsing authors section: {str(e)}")
        return authors
    
    def _parse_references(self, soup) -> List[Dict]:
        """Parse reference information from the TEI XML."""
        references = []
        try:
            for ref in soup.find_all('biblStruct'):
                try:
                    # Extract basic reference data
                    ref_data = {
                        'title': self._extract_text(ref.find('title')),
                        'authors': [],
                        'year': self._extract_text(ref.find('date')),
                        'doi': None
                    }
                    
                    # Extract authors
                    for author in ref.find_all(['author', 'editor']):
                        persname = author.find('persName')
                        if persname:
                            firstname = self._extract_text(persname.find('forename'))
                            lastname = self._extract_text(persname.find('surname'))
                            if firstname or lastname:
                                ref_data['authors'].append({
                                    'firstname': firstname,
                                    'lastname': lastname
                                })
                    
                    # Extract DOI
                    idno = ref.find('idno', type='DOI')
                    if idno:
                        ref_data['doi'] = self._extract_text(idno)
                    
                    references.append(ref_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing individual reference: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error parsing references section: {str(e)}")
        
        return references

# Global instance
_grobid_client: Optional[GrobidClient] = None

def get_grobid_client() -> GrobidClient:
    """Get or create the GROBID client instance."""
    global _grobid_client
    if _grobid_client is None:
        _grobid_client = GrobidClient()
    return _grobid_client 