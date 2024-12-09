import requests
from config import settings
import json
import os
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrobidClient:
    def __init__(self, base_url: str = settings.GROBID_URL):
        self.base_url = base_url

    def _extract_text(self, element) -> str:
        """Extract text from an XML element, handling None cases."""
        return element.get_text().strip() if element else ""

    def _parse_authors(self, soup) -> List[Dict[str, str]]:
        """Parse author information from the TEI XML."""
        authors = []
        try:
            # Try to find authors in the header first
            header = soup.find('teiHeader')
            if header:
                author_elements = header.find_all(['author', 'editor'])
                for author in author_elements:
                    try:
                        # Get persName info
                        persname = author.find('persName')
                        if not persname:
                            continue

                        # Extract name components
                        firstname = self._extract_text(persname.find('forename'))
                        lastname = self._extract_text(persname.find('surname'))
                        
                        # Get affiliation info
                        affiliation = author.find('affiliation')
                        org_name = self._extract_text(affiliation.find('orgName')) if affiliation else None
                        
                        # Get email
                        email = self._extract_text(author.find('email'))
                        
                        # Get ORCID if available
                        idno = author.find('idno', type='ORCID')
                        orcid = self._extract_text(idno) if idno else None

                        author_data = {
                            "firstname": firstname,
                            "lastname": lastname,
                            "email": email if email else None,
                            "affiliation": org_name,
                            "orcid": orcid
                        }
                        if firstname or lastname:  # Only add if at least one name component exists
                            authors.append(author_data)
                    except Exception as e:
                        logger.warning(f"Error parsing individual author: {str(e)}")
                        continue

        except Exception as e:
            logger.warning(f"Error parsing authors section: {str(e)}")
        return authors

    def _parse_date(self, soup) -> Optional[str]:
        """Parse publication date from the TEI XML."""
        try:
            date = soup.find('date', type='published')
            if date:
                when = date.get('when')
                if when:
                    # Try to parse and format the date
                    try:
                        parsed_date = datetime.strptime(when, '%Y-%m-%d')
                        return str(parsed_date.year)
                    except ValueError:
                        # If full date parsing fails, try just getting the year
                        if len(when) >= 4:
                            return when[:4]
            
            # Fallback to looking for any year-like string in the header
            header = soup.find('teiHeader')
            if header:
                text = header.get_text()
                import re
                years = re.findall(r'\b(19|20)\d{2}\b', text)
                if years:
                    return years[0]
            
        except Exception as e:
            logger.warning(f"Error parsing date: {str(e)}")
        return None

    def _parse_sections(self, soup) -> List[Dict[str, str]]:
        """Parse sections from the TEI XML."""
        sections = []
        try:
            body = soup.find('body')
            if not body:
                return sections

            # Process each div that represents a section
            for div in body.find_all('div', recursive=False):
                try:
                    # Get section title
                    head = div.find('head')
                    title = self._extract_text(head) if head else "Unnamed Section"
                    
                    # Get section content
                    content_elements = []
                    for p in div.find_all(['p', 'formula', 'figure', 'table']):
                        if p.name == 'p':
                            text = self._extract_text(p)
                            if text:
                                content_elements.append(text)
                        elif p.name in ['formula', 'figure', 'table']:
                            # Mark special elements in the text
                            content_elements.append(f"[{p.name.upper()}]")
                    
                    content = "\n\n".join(content_elements)
                    
                    if content:  # Only add sections with content
                        sections.append({
                            "title": title,
                            "content": content
                        })
                except Exception as e:
                    logger.warning(f"Error parsing section: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"Error parsing sections: {str(e)}")
        return sections

    def _parse_references(self, soup) -> List[Dict[str, str]]:
        """Parse references from the TEI XML."""
        references = []
        try:
            # Look for references in the bibliography section
            for ref in soup.find_all('biblStruct'):
                try:
                    # Get basic metadata
                    title_element = ref.find('title', type='main')
                    title = self._extract_text(title_element)
                    
                    # Get DOI
                    doi = ref.find('idno', type='DOI')
                    doi = doi.text.strip() if doi else None
                    
                    # Get authors
                    authors = []
                    for author in ref.find_all('author'):
                        persname = author.find('persName')
                        if persname:
                            firstname = self._extract_text(persname.find('forename'))
                            lastname = self._extract_text(persname.find('surname'))
                            if firstname or lastname:
                                authors.append({"firstname": firstname, "lastname": lastname})
                    
                    # Get year
                    date = ref.find('date')
                    year = self._extract_text(date) if date else None
                    if not year and date:
                        year = date.get('when', '')[:4]  # Try to get year from 'when' attribute
                    
                    # Get journal/conference info
                    venue = ref.find(['title', 'meeting'], type='journal')
                    venue_name = self._extract_text(venue) if venue else None
                    
                    ref_data = {
                        "title": title,
                        "doi": doi,
                        "authors": authors,
                        "year": year,
                        "venue": venue_name,
                        "abstract": ""  # Will be populated later when fetching reference details
                    }
                    
                    if title:  # Only add references with at least a title
                        references.append(ref_data)
                except Exception as e:
                    logger.warning(f"Error parsing individual reference: {str(e)}")
                    continue
        except Exception as e:
            logger.warning(f"Error parsing references section: {str(e)}")
        return references

    def _parse_body_text(self, soup) -> str:
        """Parse the main body text from the TEI XML."""
        try:
            body = soup.find('body')
            if not body:
                logger.warning("No body section found in the document")
                return ""
            
            # Extract text from paragraphs, excluding figures, tables, and formulas
            paragraphs = []
            for div in body.find_all(['div', 'p']):
                try:
                    if div.name == 'div':
                        for p in div.find_all('p', recursive=False):
                            text = self._extract_text(p)
                            if text:
                                paragraphs.append(text)
                    else:
                        text = self._extract_text(div)
                        if text:
                            paragraphs.append(text)
                except Exception as e:
                    logger.warning(f"Error parsing paragraph: {str(e)}")
                    continue
            
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.warning(f"Error parsing body text: {str(e)}")
            return ""

    def process_pdf(self, pdf_path: str) -> dict:
        """Process a PDF file using GROBID and return structured data."""
        url = f"{self.base_url}/api/processFulltextDocument"
        
        try:
            # Check if file exists and is readable
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not os.access(pdf_path, os.R_OK):
                raise PermissionError(f"Cannot read PDF file: {pdf_path}")
            
            # Process with GROBID
            with open(pdf_path, 'rb') as pdf_file:
                files = {'input': pdf_file}
                response = requests.post(url, files=files, timeout=30)
                response.raise_for_status()
                
                # Parse the TEI XML response
                soup = BeautifulSoup(response.text, 'xml')
                if not soup.find('TEI'):
                    logger.warning("No TEI element found in GROBID response")
                
                # Extract basic metadata with error handling
                title = self._extract_text(soup.find('title', type='main'))
                if not title:
                    logger.warning("No title found in document")
                    title = os.path.splitext(os.path.basename(pdf_path))[0]
                
                abstract = self._extract_text(soup.find('abstract'))
                if not abstract:
                    logger.warning("No abstract found in document")
                
                # Get enhanced metadata
                authors = self._parse_authors(soup)
                year = self._parse_date(soup)
                sections = self._parse_sections(soup)
                body_text = self._parse_body_text(soup)
                references = self._parse_references(soup)
                
                # Log processing summary
                logger.info(f"Processed PDF: {title}")
                logger.info(f"Found {len(authors)} authors")
                logger.info(f"Found {len(sections)} sections")
                logger.info(f"Found {len(references)} references")
                logger.info(f"Body text length: {len(body_text)} characters")
                
                return {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "sections": sections,
                    "body_text": body_text,
                    "references": references
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with GROBID: {str(e)}")
            raise Exception(f"Error processing PDF with GROBID: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise Exception(f"Error processing PDF: {str(e)}")

    def save_metadata(self, metadata: dict, filename: str):
        """Save extracted metadata to a JSON file."""
        try:
            output_path = os.path.join(settings.metadata_dir_path, f"{filename}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata to {output_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            raise Exception(f"Error saving metadata: {str(e)}") 