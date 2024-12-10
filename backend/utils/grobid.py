import requests
from config import settings
import json
import os
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrobidClient:
    """Enhanced GROBID client with optimized configuration for better extraction quality."""
    
    # GROBID API endpoints
    PROCESS_HEADER_ENDPOINT = "/api/processHeaderDocument"
    PROCESS_FULLTEXT_ENDPOINT = "/api/processFulltextDocument"
    PROCESS_REFERENCES_ENDPOINT = "/api/processReferences"
    
    # Consolidation options
    CONSOLIDATION_OPTIONS = {
        'no_consolidation': 0,
        'light_consolidation': 1,
        'full_consolidation': 2
    }

    def __init__(self, base_url: str = settings.GROBID_URL):
        self.base_url = base_url.rstrip('/')
        # Default configuration for optimal extraction
        self.default_config = {
            'consolidateHeader': 2,  # Full consolidation for header
            'consolidateCitations': 1,  # Light consolidation for citations
            'includeRawCitations': 1,  # Include raw citations
            'includeRawAffiliations': 1,  # Include raw affiliations
            'teiCoordinates': 1,  # Include coordinates for better parsing
            'segmentSentences': 1,  # Segment sentences in paragraphs
            'consolidateOtherPublications': 1,  # Consolidate other mentioned publications
            'consolidateCrossRef': 1,  # Use CrossRef for consolidation
        }

    def _call_grobid_api(self, endpoint: str, pdf_file, config: Dict = None) -> str:
        """Make a call to GROBID API with error handling and retries."""
        url = f"{self.base_url}{endpoint}"
        
        # Merge default config with any custom config
        params = self.default_config.copy()
        if config:
            params.update(config)
        
        try:
            # First try with full consolidation
            response = requests.post(
                url,
                files={'input': pdf_file},
                data=params,
                timeout=60  # Increased timeout for better processing
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.warning(f"Full consolidation failed, trying with light consolidation: {str(e)}")
            # If full consolidation fails, try with light consolidation
            params['consolidateHeader'] = 1
            params['consolidateCitations'] = 1
            try:
                response = requests.post(
                    url,
                    files={'input': pdf_file},
                    data=params,
                    timeout=45
                )
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"Light consolidation failed, trying without consolidation: {str(e)}")
                # If light consolidation fails, try without consolidation
                params['consolidateHeader'] = 0
                params['consolidateCitations'] = 0
                response = requests.post(
                    url,
                    files={'input': pdf_file},
                    data=params,
                    timeout=30
                )
                response.raise_for_status()
                return response.text

    def _extract_text(self, element) -> str:
        """Extract clean text from an XML element."""
        if not element:
            return ""
        
        # Get all text, including nested elements
        text = element.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text

    def _parse_authors(self, soup) -> List[Dict[str, str]]:
        """Parse author information from the TEI XML."""
        authors = []
        try:
            # First try the analytic section which contains the main paper authors
            analytic = soup.find('sourceDesc').find('biblStruct').find('analytic')
            if analytic:
                author_elements = analytic.find_all('author')
                for author in author_elements:
                    author_data = self._extract_author_data(author)
                    if author_data:
                        authors.append(author_data)
                        
            # If no authors found, try the monogr section
            if not authors:
                monogr = soup.find('sourceDesc').find('biblStruct').find('monogr')
                if monogr:
                    author_elements = monogr.find_all('author')
                    for author in author_elements:
                        author_data = self._extract_author_data(author)
                        if author_data:
                            authors.append(author_data)
            
            # Log the results
            if authors:
                logger.info(f"Successfully extracted {len(authors)} authors")
            else:
                logger.warning("No authors found in the document")
                
        except Exception as e:
            logger.error(f"Error parsing authors: {str(e)}", exc_info=True)
            
        return authors
        
    def _extract_author_data(self, author_elem) -> Optional[Dict[str, str]]:
        """Extract structured data from an author element."""
        try:
            # Get the persName element
            persname = author_elem.find('persName')
            if not persname:
                return None
                
            # Extract name components
            firstname = ""
            lastname = ""
            
            # Handle forename(s)
            forenames = persname.find_all('forename')
            if forenames:
                firstname = ' '.join(self._extract_text(f) for f in forenames if self._extract_text(f))
            
            # Handle surname
            surname = persname.find('surname')
            if surname:
                lastname = self._extract_text(surname)
                
            # Basic validation
            if not firstname and not lastname:
                return None
                
            # Additional validation to prevent false positives
            name = f"{firstname} {lastname}".lower()
            non_person_indicators = {
                'university', 'institute', 'college', 'school', 'department',
                'lab', 'laboratory', 'center', 'centre', 'hospital', 'corp',
                'corporation', 'inc', 'ltd', 'limited', 'city', 'town',
                'delhi', 'paris', 'london', 'beijing', 'tokyo', 'research',
                'group', 'team', 'division', 'faculty', 'sciences', 'engineering'
            }
            
            if any(indicator in name.split() for indicator in non_person_indicators):
                logger.warning(f"Skipping non-person name: {name}")
                return None
            
            # Get affiliations with improved extraction
            affiliations = []
            seen_affiliations = set()  # To prevent duplicates
            
            for affiliation in author_elem.find_all('affiliation'):
                aff_data = {}
                
                # Get institution name with better validation
                institution = None
                for inst_tag in ['institution', 'orgName']:
                    inst_elem = affiliation.find(inst_tag)
                    if inst_elem:
                        inst_text = self._extract_text(inst_elem)
                        # Validate that institution name is not the same as author name
                        if inst_text.lower() not in name.lower():
                            institution = inst_text
                            break
                
                if institution:
                    aff_data['institution'] = institution
                
                # Get department
                dept = affiliation.find('department')
                if dept:
                    dept_text = self._extract_text(dept)
                    if dept_text.lower() not in name.lower():  # Validate department
                        aff_data['department'] = dept_text
                
                # Get address components
                address = affiliation.find('address')
                if address:
                    addr_parts = []
                    
                    # Extract settlement (city)
                    settlement = address.find('settlement')
                    if settlement:
                        addr_parts.append(self._extract_text(settlement))
                    
                    # Extract region (state/province)
                    region = address.find('region')
                    if region:
                        addr_parts.append(self._extract_text(region))
                    
                    # Extract country
                    country = address.find('country')
                    if country:
                        addr_parts.append(self._extract_text(country))
                    
                    if addr_parts:
                        aff_data['address'] = ', '.join(addr_parts)
                
                # Only add non-empty, unique affiliations
                if aff_data:
                    # Create a hash of the affiliation data to check uniqueness
                    aff_hash = tuple(sorted(aff_data.items()))
                    if aff_hash not in seen_affiliations:
                        seen_affiliations.add(aff_hash)
                        affiliations.append(aff_data)
            
            # Get email
            email = None
            email_elem = author_elem.find('email')
            if email_elem:
                email = self._extract_text(email_elem)
                if not ('@' in email and '.' in email.split('@')[1]):
                    email = None
            
            # Only return if we have valid name and affiliation data
            if firstname or lastname:
                author_data = {
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": email,
                    "affiliations": affiliations if affiliations else None
                }
                logger.info(f"Successfully extracted author: {firstname} {lastname}")
                return author_data
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting author data: {str(e)}")
            return None

    def _clean_title(self, title: str) -> str:
        """Clean and normalize a title string."""
        if not title:
            return ""
            
        # Remove common suffixes that shouldn't be part of the title
        suffixes_to_remove = [
            r'\s+in\s+ICML\s*\d*',
            r'\s+in\s+NIPS\s*\d*',
            r'\s+in\s+ICLR\s*\d*',
            r'\s+in\s+AAAI\s*\d*',
            r'\s+in\s+ICCV\s*\d*',
            r'\s+in\s+CVPR\s*\d*',
            r'\s+in\s+arXiv\s*\d*',
            r'\s+in\s+proceedings\s+of\s+.*',
            r'\s+Technical\s+Report\s*.*$',
            r'\s*\([^)]*\)\s*$',  # Remove trailing parentheses
            r'\s*\.\s*$',  # Remove trailing period
        ]
        
        cleaned_title = title
        for suffix in suffixes_to_remove:
            cleaned_title = re.sub(suffix, '', cleaned_title, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned_title = ' '.join(cleaned_title.split())
        
        return cleaned_title.strip()

    def _parse_sections(self, soup) -> List[Dict[str, str]]:
        """Parse sections from the TEI XML with improved structure handling."""
        sections = []
        try:
            # Get the main text body
            body = soup.find('body')
            if not body:
                logger.warning("No body found in document")
                return sections

            # First pass: identify main sections and build hierarchy
            current_section = None
            section_stack = []  # Keep track of section hierarchy
            
            for div in body.find_all(['div'], recursive=True):
                try:
                    # Get section level from n attribute or div depth
                    section_level = 1  # Default to top level
                    if div.get('n'):
                        try:
                            section_level = int(div.get('n').split('.')[0])
                        except (ValueError, IndexError):
                            pass
                    
                    # Get section head/title
                    head = div.find('head', recursive=False)
                    if not head:
                        continue  # Skip sections without headers
                        
                    title = self._extract_text(head)
                    if not title:
                        continue  # Skip sections without titles
                        
                    # Skip unwanted sections
                    if self._should_skip_section(title):
                        continue
                    
                    # Get section content
                    content = self._extract_section_content(div)
                    if not content.strip():
                        continue  # Skip empty sections
                    
                    # Create section object
                    section = {
                        "title": title,
                        "content": content,
                        "level": section_level,
                        "subsections": []
                    }
                    
                    # Handle section hierarchy
                    if not section_stack:
                        # First section
                        sections.append(section)
                        section_stack.append(section)
                    else:
                        # Find appropriate parent section
                        while section_stack and section_stack[-1]["level"] >= section_level:
                            section_stack.pop()
                            
                        if section_stack:
                            # Add as subsection
                            section_stack[-1]["subsections"].append(section)
                        else:
                            # Top level section
                            sections.append(section)
                            
                        section_stack.append(section)
                        
                except Exception as e:
                    logger.warning(f"Error processing section element: {str(e)}")
                    continue
            
            # Flatten sections if needed (depends on your requirements)
            flattened_sections = self._flatten_sections(sections)
            
            logger.info(f"Successfully extracted {len(flattened_sections)} sections")
            return flattened_sections
            
        except Exception as e:
            logger.error(f"Error parsing sections: {str(e)}", exc_info=True)
            return sections

    def _should_skip_section(self, title: str) -> bool:
        """Determine if a section should be skipped based on its title."""
        # Convert to lowercase for comparison
        title_lower = title.lower().strip()
        
        # Skip empty or unnamed sections
        if not title_lower or title_lower == "unnamed section":
            return True
            
        # Skip common unwanted sections
        skip_patterns = {
            r'^end\s+for\s*$',
            r'^end\s+if\s*$',
            r'^begin\s*$',
            r'^end\s*$',
            r'^model\s*$',
            r'^\d+(\.\d+)*\s*$',  # Just numbers
            r'^figure\s+\d+\s*:?.*$',  # Figure captions
            r'^table\s+\d+\s*:?.*$',  # Table captions
            r'^algorithm\s+\d+\s*:?.*$',  # Algorithm captions
        }
        
        return any(re.match(pattern, title_lower) for pattern in skip_patterns)

    def _extract_section_content(self, div) -> str:
        """Extract and clean section content."""
        content_parts = []
        
        # Skip the head element as it's already processed
        for elem in div.find_all(['p', 'formula', 'figure', 'table'], recursive=False):
            if elem.name == 'p':
                text = self._extract_text(elem)
                if text:
                    content_parts.append(text)
            elif elem.name == 'formula':
                formula_text = self._extract_text(elem)
                if formula_text:
                    content_parts.append(f"[FORMULA: {formula_text}]")
            elif elem.name == 'figure':
                caption = elem.find('figDesc')
                if caption:
                    content_parts.append(f"[FIGURE: {self._extract_text(caption)}]")
                else:
                    content_parts.append("[FIGURE]")
            elif elem.name == 'table':
                content_parts.append("[TABLE]")
        
        # Also get text directly under the div
        for text in div.find_all(text=True, recursive=False):
            cleaned_text = text.strip()
            if cleaned_text:
                content_parts.append(cleaned_text)
        
        return '\n\n'.join(content_parts)

    def _flatten_sections(self, sections: List[Dict], level: int = 1) -> List[Dict]:
        """Flatten nested sections into a linear list while preserving hierarchy information."""
        flattened = []
        for section in sections:
            # Create a copy without subsections
            section_copy = {
                "title": section["title"],
                "content": section["content"],
                "level": level
            }
            flattened.append(section_copy)
            
            # Process subsections
            if section.get("subsections"):
                flattened.extend(self._flatten_sections(section["subsections"], level + 1))
        
        return flattened

    def _parse_date(self, soup) -> Optional[str]:
        """Parse publication date from the TEI XML."""
        try:
            # Try to find date in multiple locations
            date_locations = [
                (soup.find('date', type='published'), 'published date'),
                (soup.find('date', type='submission'), 'submission date'),
                (soup.find('date', type='preprint'), 'preprint date'),
                (soup.find('publicationStmt').find('date') if soup.find('publicationStmt') else None, 'publication statement date'),
                (soup.find('sourceDesc').find('date') if soup.find('sourceDesc') else None, 'source date')
            ]

            for date_elem, desc in date_locations:
                if date_elem:
                    # Try 'when' attribute first
                    when = date_elem.get('when')
                    if when:
                        try:
                            # Try to parse full date
                            parsed_date = datetime.strptime(when, '%Y-%m-%d')
                            logger.info(f"Found {desc}: {parsed_date.year}")
                            return str(parsed_date.year)
                        except ValueError:
                            # If full date parsing fails, try just getting the year
                            if len(when) >= 4:
                                logger.info(f"Found {desc} year: {when[:4]}")
                                return when[:4]
                    
                    # If no 'when' attribute, try text content
                    text = self._extract_text(date_elem)
                    if text:
                        # Look for year in text
                        import re
                        year_match = re.search(r'\b(19|20)\d{2}\b', text)
                        if year_match:
                            logger.info(f"Found year in {desc} text: {year_match.group()}")
                            return year_match.group()

            # If no date found in specific elements, try searching in the header
            header = soup.find('teiHeader')
            if header:
                text = header.get_text()
                years = re.findall(r'\b(19|20)\d{2}\b', text)
                if years:
                    # Sort years to get the most likely publication year (usually the latest)
                    years.sort(reverse=True)
                    logger.info(f"Found year in header text: {years[0]}")
                    return years[0]
            
            logger.warning("No date found in document")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}", exc_info=True)
            return None

    def _parse_references(self, soup) -> List[Dict[str, str]]:
        """Parse references from the TEI XML."""
        references = []
        try:
            # Look for references in the bibliography section
            for ref in soup.find_all('biblStruct'):
                try:
                    # Extract title with fallbacks
                    title = None
                    # Try analytic title first (for papers)
                    if ref.find('analytic'):
                        title_elem = ref.find('analytic').find('title', type='main')
                        if title_elem:
                            title = self._clean_title(self._extract_text(title_elem))
                    
                    # If no analytic title, try monograph title (for books)
                    if not title and ref.find('monogr'):
                        title_elem = ref.find('monogr').find('title', type=['main', 'm'])
                        if title_elem:
                            title = self._clean_title(self._extract_text(title_elem))
                    
                    # If still no title, try any title
                    if not title:
                        title_elem = ref.find('title')
                        if title_elem:
                            title = self._clean_title(self._extract_text(title_elem))
                    
                    # Get DOI and arXiv ID
                    identifiers = {}
                    for idno in ref.find_all('idno'):
                        id_type = idno.get('type', '').lower()
                        id_text = self._extract_text(idno)
                        if id_text:
                            identifiers[id_type] = id_text
                    
                    # Get authors using the same robust extraction logic
                    authors = []
                    for author in ref.find_all('author'):
                        author_data = self._extract_author_data(author)
                        if author_data:
                            authors.append({
                                "firstname": author_data['firstname'],
                                "lastname": author_data['lastname']
                            })
                    
                    # Get year with enhanced extraction
                    year = None
                    
                    # First try explicit dates
                    date_types = ['published', 'submission', 'completion', 'print', 'electronic']
                    for date_type in date_types:
                        if year:
                            break
                        date_elem = ref.find('date', type=date_type)
                        if date_elem:
                            year = self._extract_year_from_date(date_elem)
                    
                    # If no year found, try dates without type
                    if not year:
                        for date_elem in ref.find_all('date'):
                            year = self._extract_year_from_date(date_elem)
                            if year:
                                break
                    
                    # If still no year, try imprint date
                    if not year and ref.find('imprint'):
                        date_elem = ref.find('imprint').find('date')
                        if date_elem:
                            year = self._extract_year_from_date(date_elem)
                    
                    # If still no year, try extracting from identifiers or text
                    if not year:
                        # Try arXiv ID (format: YYMM.xxxxx)
                        arxiv_id = identifiers.get('arxiv', '')
                        if arxiv_id and len(arxiv_id) >= 2:
                            try:
                                yy = int(arxiv_id[:2])
                                year = f"20{yy}" if yy < 91 else f"19{yy}"
                            except ValueError:
                                pass
                        
                        # Try extracting from any text content
                        if not year:
                            text = ref.get_text()
                            year_match = re.search(r'\b(19|20)\d{2}\b', text)
                            if year_match:
                                year = year_match.group()
                    
                    # Get venue information with fallbacks
                    venue_info = self._extract_venue_info(ref)
                    
                    # Construct reference data
                    ref_data = {
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "doi": identifiers.get('doi'),
                        "arxiv": identifiers.get('arxiv'),
                        "venue": venue_info.get('name'),
                        "venue_type": venue_info.get('type'),
                        "pages": venue_info.get('pages'),
                        "volume": venue_info.get('volume'),
                        "issue": venue_info.get('issue'),
                        "publisher": venue_info.get('publisher')
                    }
                    
                    # Add reference if it has minimum required information
                    if title or (authors and year):
                        references.append(ref_data)
                        logger.info(f"Parsed reference: {title[:50] if title else 'Untitled'} ({year if year else 'Year unknown'})")
                    else:
                        logger.warning(f"Skipping reference with insufficient data: {ref_data}")
                        
                except Exception as e:
                    logger.warning(f"Error parsing individual reference: {str(e)}", exc_info=True)
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing references section: {str(e)}", exc_info=True)
            
        return references

    def _extract_year_from_date(self, date_elem) -> Optional[str]:
        """Extract year from a date element with multiple fallback methods."""
        if not date_elem:
            return None
            
        # Try 'when' attribute first
        when = date_elem.get('when')
        if when:
            # Try full date format
            try:
                return str(datetime.strptime(when, '%Y-%m-%d').year)
            except ValueError:
                # Try just the year
                if len(when) >= 4:
                    return when[:4]
        
        # Try text content
        text = self._extract_text(date_elem)
        if text:
            # Look for year in text
            year_match = re.search(r'\b(19|20)\d{2}\b', text)
            if year_match:
                return year_match.group()
        
        return None

    def _extract_venue_info(self, ref) -> Dict[str, str]:
        """Extract venue information from a reference."""
        venue_info = {}
        
        try:
            # Try to get venue name
            for venue_elem in [
                ref.find('title', type='journal'),
                ref.find('meeting'),
                ref.find('monogr', recursive=False)
            ]:
                if venue_elem:
                    if venue_elem.name == 'monogr':
                        title_elem = venue_elem.find('title')
                        if title_elem:
                            venue_info['name'] = self._extract_text(title_elem)
                            venue_info['type'] = 'book'
                    else:
                        venue_info['name'] = self._extract_text(venue_elem)
                        venue_info['type'] = 'journal' if venue_elem.get('type') == 'journal' else 'conference'
                    break
            
            # Get publisher
            publisher = ref.find('publisher')
            if publisher:
                venue_info['publisher'] = self._extract_text(publisher)
            
            # Get pages
            biblScope = ref.find('biblScope', unit='page')
            if biblScope:
                start = biblScope.get('from')
                end = biblScope.get('to')
                if start and end:
                    venue_info['pages'] = f"{start}-{end}"
                else:
                    venue_info['pages'] = self._extract_text(biblScope)
            
            # Get volume/issue
            for unit in ['volume', 'issue']:
                elem = ref.find('biblScope', unit=unit)
                if elem:
                    venue_info[unit] = self._extract_text(elem)
            
        except Exception as e:
            logger.warning(f"Error extracting venue info: {str(e)}")
        
        return venue_info

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
        """Process a PDF file using GROBID with optimized extraction."""
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not os.access(pdf_path, os.R_OK):
                raise PermissionError(f"Cannot read PDF file: {pdf_path}")
            
            # Process the PDF in multiple steps for better accuracy
            with open(pdf_path, 'rb') as pdf_file:
                # Step 1: Process header separately for better metadata
                header_response = self._call_grobid_api(
                    self.PROCESS_HEADER_ENDPOINT,
                    pdf_file,
                    {'consolidateHeader': 2}  # Full consolidation for header
                )
                header_soup = BeautifulSoup(header_response, 'xml')
                
                # Step 2: Process full text
                pdf_file.seek(0)  # Reset file pointer
                fulltext_response = self._call_grobid_api(
                    self.PROCESS_FULLTEXT_ENDPOINT,
                    pdf_file
                )
                fulltext_soup = BeautifulSoup(fulltext_response, 'xml')
                
                # Step 3: Process references separately for better accuracy
                pdf_file.seek(0)  # Reset file pointer
                refs_response = self._call_grobid_api(
                    self.PROCESS_REFERENCES_ENDPOINT,
                    pdf_file,
                    {'consolidateCitations': 2}  # Full consolidation for references
                )
                refs_soup = BeautifulSoup(refs_response, 'xml')
                
                # Extract metadata using the most accurate source
                title = (
                    self._extract_text(header_soup.find('title', type='main')) or
                    self._extract_text(fulltext_soup.find('title', type='main')) or
                    os.path.splitext(os.path.basename(pdf_path))[0]
                )
                
                # Get authors from header if available, fallback to fulltext
                authors = (
                    self._parse_authors(header_soup) or
                    self._parse_authors(fulltext_soup)
                )
                
                # Get other metadata
                year = self._parse_date(header_soup) or self._parse_date(fulltext_soup)
                abstract = self._extract_text(header_soup.find('abstract') or fulltext_soup.find('abstract'))
                
                # Get content from full text
                sections = self._parse_sections(fulltext_soup)
                body_text = self._parse_body_text(fulltext_soup)
                
                # Get references from dedicated reference processing
                references = self._parse_references(refs_soup) or self._parse_references(fulltext_soup)
                
                # Log processing results
                logger.info(f"Successfully processed PDF: {title}")
                logger.info(f"Found {len(authors)} authors")
                logger.info(f"Found {len(sections)} sections")
                logger.info(f"Found {len(references)} references")
                
                return {
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "abstract": abstract,
                    "sections": sections,
                    "body_text": body_text,
                    "references": references
                }
                
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            raise

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