"""
Bank Statement Preprocessing using Veryfi API
Specifically designed for Wells Fargo and other bank statement formats
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from decimal import Decimal, InvalidOperation

# Add the current directory to Python path to import our common module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Preprocess.PreprocressCommon import (
    VeryfiConfig, 
    DocumentProcessor, 
    create_output_directory, 
    generate_output_filename,
    logger
)

class BankStatementProcessor(DocumentProcessor):
    """Specialized processor for bank statements"""
    
    def __init__(self, config: VeryfiConfig):
        super().__init__(config)
        self.statement_info = {}
        self.transactions = []
    
    def process_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Process a bank statement PDF and extract structured data"""
        # Process with Veryfi API using bank statement category
        response = self.process_document(file_path, categories=['Bank Statement'])
        
        # Extract and structure the data
        self.statement_info = self._extract_statement_info(response)
        self.transactions = self._extract_transactions(response)
        
        # Add some post-processing
        self._validate_and_clean_transactions()
        
        return {
            'statement_info': self.statement_info,
            'transactions': self.transactions,
            'raw_response': response
        }
    
    def _extract_statement_info(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract general statement information"""
        info = self.extract_basic_info(response)
        
        # Add bank-specific fields
        info.update({
            'account_number': self._extract_account_number(response),
            'statement_period': self._extract_statement_period(response),
            'opening_balance': response.get('opening_balance'),
            'closing_balance': response.get('closing_balance'),
            'bank_name': self._identify_bank(response),
            'statement_date': response.get('statement_date', response.get('date'))
        })
        
        return info
    
    def _extract_transactions(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and structure transaction data"""
        transactions = []
        
        # Get line items (transactions) from Veryfi response
        line_items = response.get('line_items', [])
        
        for item in line_items:
            transaction = {
                'date': self._parse_transaction_date(item.get('date')),
                'description': item.get('description', '').strip(),
                'amount': self._parse_amount(item.get('total', 0)),
                'transaction_type': self._determine_transaction_type(item),
                'category': item.get('category', 'Unknown'),
                'reference': item.get('reference', ''),
                'balance': self._parse_amount(item.get('balance'))
            }
            
            # Add debit/credit classification
            transaction['is_debit'] = transaction['amount'] < 0
            transaction['is_credit'] = transaction['amount'] > 0
            
            transactions.append(transaction)
        
        # Sort transactions by date
        transactions.sort(key=lambda x: x['date'] if x['date'] else datetime.min)
        
        return transactions
    
    def _extract_account_number(self, response: Dict[str, Any]) -> Optional[str]:
        """Extract account number from the response"""
        # Try different fields where account number might be stored
        account_fields = ['account_number', 'account', 'account_id']
        
        for field in account_fields:
            if field in response and response[field]:
                return str(response[field])
        
        # Try to extract from text using pattern matching
        ocr_text = response.get('ocr_text', '')
        import re
        
        # Wells Fargo account number pattern (adjust as needed)
        patterns = [
            r'Account\s+(?:Number|#)?\s*:?\s*(\d{4,12})',
            r'Acct\s*:?\s*(\d{4,12})',
            r'Account\s+(\d{4,12})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, ocr_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_statement_period(self, response: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """Extract statement period dates"""
        return {
            'start_date': response.get('statement_start_date'),
            'end_date': response.get('statement_end_date', response.get('date'))
        }
    
    def _identify_bank(self, response: Dict[str, Any]) -> str:
        """Identify the bank from the document"""
        vendor_info = response.get('vendor', {})
        vendor_name = vendor_info.get('name', '').lower()
        
        # Check common bank identifiers
        if 'wells fargo' in vendor_name:
            return 'Wells Fargo'
        elif 'chase' in vendor_name:
            return 'JPMorgan Chase'
        elif 'bank of america' in vendor_name or 'bofa' in vendor_name:
            return 'Bank of America'
        elif 'citibank' in vendor_name or 'citi' in vendor_name:
            return 'Citibank'
        
        # If not found in vendor, check OCR text
        ocr_text = response.get('ocr_text', '').lower()
        if 'wells fargo' in ocr_text:
            return 'Wells Fargo'
        
        return vendor_info.get('name', 'Unknown Bank')
    
    def _parse_transaction_date(self, date_str: str) -> Optional[datetime]:
        """Parse transaction date from various formats"""
        if not date_str:
            return None
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%d/%m/%Y',
            '%B %d, %Y',
            '%b %d, %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_amount(self, amount) -> float:
        """Parse monetary amount handling various formats"""
        if amount is None:
            return 0.0
        
        if isinstance(amount, (int, float)):
            return float(amount)
        
        if isinstance(amount, str):
            # Remove currency symbols and spaces
            amount = amount.replace('$', '').replace(',', '').replace(' ', '')
            
            # Handle parentheses for negative amounts
            if amount.startswith('(') and amount.endswith(')'):
                amount = '-' + amount[1:-1]
            
            try:
                return float(amount)
            except ValueError:
                logger.warning(f"Could not parse amount: {amount}")
                return 0.0
        
        return 0.0
    
    def _determine_transaction_type(self, item: Dict[str, Any]) -> str:
        """Determine transaction type based on description and amount"""
        description = item.get('description', '').lower()
        amount = self._parse_amount(item.get('total', 0))
        
        # Categorize based on common patterns
        if 'deposit' in description or 'credit' in description:
            return 'Credit'
        elif 'withdrawal' in description or 'debit' in description:
            return 'Debit'
        elif 'check' in description:
            return 'Check'
        elif 'atm' in description:
            return 'ATM'
        elif 'transfer' in description:
            return 'Transfer'
        elif 'fee' in description:
            return 'Fee'
        elif amount < 0:
            return 'Debit'
        else:
            return 'Credit'
    
    def _validate_and_clean_transactions(self):
        """Validate and clean transaction data"""
        cleaned_transactions = []
        
        for transaction in self.transactions:
            # Skip transactions with missing critical data
            if not transaction.get('description') or transaction.get('description').strip() == '':
                logger.warning("Skipping transaction with empty description")
                continue
            
            # Clean description
            transaction['description'] = transaction['description'].strip()
            
            # Ensure amount is properly formatted
            if isinstance(transaction['amount'], str):
                transaction['amount'] = self._parse_amount(transaction['amount'])
            
            cleaned_transactions.append(transaction)
        
        self.transactions = cleaned_transactions
    
    def export_to_csv(self, output_path: str) -> str:
        """Export transactions to CSV format"""
        if not self.transactions:
            raise ValueError("No transactions to export. Process a document first.")
        
        # Create DataFrame
        df = pd.DataFrame(self.transactions)
        
        # Reorder columns for better readability
        column_order = [
            'date', 'description', 'amount', 'transaction_type', 
            'is_debit', 'is_credit', 'category', 'reference', 'balance'
        ]
        
        # Only include columns that exist
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        # Format date column
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Transactions exported to: {output_path}")
        
        return output_path
    
    def export_to_excel(self, output_path: str) -> str:
        """Export transactions to Excel format with multiple sheets"""
        if not self.transactions:
            raise ValueError("No transactions to export. Process a document first.")
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Transactions sheet
            transactions_df = pd.DataFrame(self.transactions)
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Transactions', 
                    'Total Credits', 
                    'Total Debits', 
                    'Net Amount',
                    'Date Range'
                ],
                'Value': [
                    len(self.transactions),
                    len([t for t in self.transactions if t.get('is_credit', False)]),
                    len([t for t in self.transactions if t.get('is_debit', False)]),
                    sum(t.get('amount', 0) for t in self.transactions),
                    f"{min(t.get('date', datetime.now()) for t in self.transactions if t.get('date'))} to {max(t.get('date', datetime.now()) for t in self.transactions if t.get('date'))}" if self.transactions else "N/A"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Statement Info sheet
            if self.statement_info:
                info_df = pd.DataFrame([self.statement_info])
                info_df.to_excel(writer, sheet_name='Statement Info', index=False)
        
        logger.info(f"Data exported to Excel: {output_path}")
        return output_path

def main():
    """Main function to process a bank statement"""
    # Initialize configuration
    config = VeryfiConfig()
    
    if not config.is_configured():
        logger.error("Veryfi credentials not configured!")
        logger.info("Please set the following environment variables:")
        logger.info("- VERYFI_CLIENT_ID")
        logger.info("- VERYFI_CLIENT_SECRET") 
        logger.info("- VERYFI_USERNAME")
        logger.info("- VERYFI_API_KEY")
        return
    
    # Initialize processor
    processor = BankStatementProcessor(config)
    
    # File path from the user's request
    pdf_path = r"D:\Development\GnS\Bank_Categorization\input\WellsFargo\bankStatement\_013125 WellsFargo.pdf"
    
    try:
        # Process the bank statement
        logger.info("Starting bank statement processing...")
        result = processor.process_bank_statement(pdf_path)
        
        # Create output directory
        output_dir = create_output_directory("output", "processed_statements")
        
        # Generate output filenames
        csv_filename = generate_output_filename(pdf_path, "transactions", "csv")
        excel_filename = generate_output_filename(pdf_path, "complete", "xlsx")
        json_filename = generate_output_filename(pdf_path, "raw_response", "json")
        
        csv_path = os.path.join(output_dir, csv_filename)
        excel_path = os.path.join(output_dir, excel_filename)
        json_path = os.path.join(output_dir, json_filename)
        
        # Export data
        processor.export_to_csv(csv_path)
        processor.export_to_excel(excel_path)
        processor.save_response_to_json(result['raw_response'], json_path)
        
        # Print summary
        logger.info("=== PROCESSING COMPLETE ===")
        logger.info(f"Statement Info: {result['statement_info']}")
        logger.info(f"Total Transactions: {len(result['transactions'])}")
        logger.info(f"Files generated:")
        logger.info(f"  - CSV: {csv_path}")
        logger.info(f"  - Excel: {excel_path}")
        logger.info(f"  - JSON: {json_path}")
        
    except Exception as e:
        logger.error(f"Error processing bank statement: {e}")
        raise

if __name__ == "__main__":
    main()
