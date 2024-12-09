import requests
from config import settings
import json
import os

class GrobidClient:
    def __init__(self, base_url: str = settings.grobid_url):
        self.base_url = base_url

    def process_pdf(self, pdf_path: str) -> dict:
        """
        Process a PDF file using GROBID and return structured data.
        """
        # Endpoint for full text extraction
        url = f"{self.base_url}/api/processFulltextDocument"
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                files = {'input': pdf_file}
                response = requests.post(url, files=files)
                response.raise_for_status()
                
                # Parse the TEI XML response and convert to our desired format
                # TODO: Implement XML parsing to extract:
                # - Title
                # - Authors
                # - Abstract
                # - Body text
                # - References
                
                return {
                    "title": "",
                    "authors": [],
                    "abstract": "",
                    "body_text": "",
                    "references": []
                }
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error processing PDF with GROBID: {str(e)}")

    def save_metadata(self, metadata: dict, filename: str):
        """
        Save extracted metadata to a JSON file.
        """
        output_path = os.path.join(settings.metadata_dir, f"{filename}.json")
        with open(output_path, 'w') as f:
            json.dump(metadata, f, indent=2) 