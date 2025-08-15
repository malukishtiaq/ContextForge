from typing import List
from app.services.parser.base import ParsedPage


class OCRProvider:
    """Base OCR provider interface for PDF text extraction."""
    
    def parse(self, pdf_path: str) -> tuple[List[ParsedPage], dict]:
        """
        Parse PDF using OCR to extract text from images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (parsed_pages, metadata)
            
        Raises:
            NotImplementedError: OCR not implemented. Enable later with a provider.
        """
        raise NotImplementedError(
            "OCR not implemented. Enable later with a provider like Tesseract, "
            "Azure Computer Vision, or Google Cloud Vision API."
        )


