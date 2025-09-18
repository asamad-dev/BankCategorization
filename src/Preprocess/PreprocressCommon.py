"""
Common preprocessing utilities for document processing using Veryfi API
"""
import os
import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file if it exists
except ImportError:
    pass  # dotenv is optional, continue without it

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

class VeryfiConfig:
    """Configuration class for Veryfi API credentials"""
    
    def __init__(self):
        # Try to get credentials from environment variables first
        self.client_id = os.getenv('VERYFI_CLIENT_ID')
        self.client_secret = os.getenv('VERYFI_CLIENT_SECRET')
        self.username = os.getenv('VERYFI_USERNAME')
        self.api_key = os.getenv('VERYFI_API_KEY')
        
        # If not found in environment, you can set them here temporarily
        # NOTE: For production, always use environment variables or secure config files
        if not all([self.client_id, self.client_secret, self.username, self.api_key]):
            logger.warning("Veryfi credentials not found in environment variables.")
            logger.info("Please set VERYFI_CLIENT_ID, VERYFI_CLIENT_SECRET, VERYFI_USERNAME, VERYFI_API_KEY")
    
    def is_configured(self) -> bool:
        """Check if all required credentials are available"""
        return all([self.client_id, self.client_secret, self.username, self.api_key])

class DocumentProcessor:
    """Base class for document processing with Veryfi"""
    
    def __init__(self, config: VeryfiConfig):
        self.config = config
        self.client = None
        if config.is_configured():
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Veryfi client"""
        try:
            import veryfi
            self.client = veryfi.Client(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                username=self.config.username,
                api_key=self.config.api_key
            )
            logger.info("Veryfi client initialized successfully")
        except ImportError:
            logger.error("Veryfi library not installed. Please run: pip install veryfi")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Veryfi client: {e}")
            raise
    
    def process_document(self, file_path: str, categories: List[str] = None) -> Dict[str, Any]:
        """Process a document using Veryfi API"""
        if not self.client:
            raise RuntimeError("Veryfi client not initialized. Check your credentials.")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            logger.info(f"Processing document: {file_path}")
            response = self.client.process_document(file_path, categories=categories or [])
            logger.info("Document processed successfully")
            return response
        except Exception as e:
            logger.error(f"Failed to process document: {e}")
            raise
    
    def save_response_to_json(self, response: Dict[str, Any], output_path: str):
        """Save Veryfi response to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(response, f, indent=2, ensure_ascii=False)
            logger.info(f"Response saved to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save response to JSON: {e}")
            raise
    
    def extract_basic_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic document information"""
        return {
            'document_type': response.get('document_type'),
            'vendor': response.get('vendor', {}).get('name'),
            'date': response.get('date'),
            'total': response.get('total'),
            'currency_code': response.get('currency_code'),
            'confidence_score': response.get('confidence_score'),
            'pages': response.get('pages', 1)
        }

def create_output_directory(base_path: str, subdirectory: str = None) -> str:
    """Create output directory if it doesn't exist"""
    if subdirectory:
        output_dir = os.path.join(base_path, subdirectory)
    else:
        output_dir = base_path
    
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def generate_output_filename(input_file: str, suffix: str, extension: str) -> str:
    """Generate output filename based on input file"""
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{suffix}_{timestamp}.{extension}"
