# Wells Fargo Bank Statement Processing with Veryfi

This project processes PDF bank statements and converts them to structured CSV/Excel data using the Veryfi API.

## Quick Start

### 1. Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Get Veryfi API Credentials
1. Sign up at: https://www.veryfi.com/
2. Go to your dashboard
3. Copy your API credentials

### 3. Configure Credentials
Choose one of these methods:

**Method A: Using .env file (Recommended)**
```bash
# Copy the example file
copy env.example .env  # Windows
# cp env.example .env    # Linux/Mac

# Edit .env with your actual credentials
```

**Method B: Environment Variables**
```powershell
# PowerShell
$env:VERYFI_CLIENT_ID='your_client_id'
$env:VERYFI_CLIENT_SECRET='your_client_secret'
$env:VERYFI_USERNAME='your_username'
$env:VERYFI_API_KEY='your_api_key'
```

### 4. Process Bank Statement
```bash
# Run the processor
python src/Preprocess/PreprocressBankStatement.py
```

## Output Files

The script will generate:
- **CSV**: `output/processed_statements/[filename]_transactions_[timestamp].csv`
- **Excel**: `output/processed_statements/[filename]_complete_[timestamp].xlsx`
- **JSON**: `output/processed_statements/[filename]_raw_response_[timestamp].json`

## What Gets Extracted

- **Transactions**: Date, Description, Amount, Type, Category
- **Statement Info**: Account number, Bank name, Statement period
- **Balance Information**: Opening and closing balances
- **Transaction Classification**: Debit/Credit, Transaction types

## Example Output Structure

### CSV Columns:
- `date`: Transaction date (YYYY-MM-DD)
- `description`: Transaction description
- `amount`: Transaction amount (negative for debits)
- `transaction_type`: Credit, Debit, Check, ATM, Transfer, Fee
- `is_debit`: Boolean
- `is_credit`: Boolean
- `category`: Transaction category
- `reference`: Reference number
- `balance`: Running balance

## Programmatic Usage

```python
from src.Preprocess.PreprocressBankStatement import BankStatementProcessor
from src.Preprocess.PreprocressCommon import VeryfiConfig

# Initialize
config = VeryfiConfig()
processor = BankStatementProcessor(config)

# Process statement
pdf_path = "path/to/statement.pdf"
result = processor.process_bank_statement(pdf_path)

# Export data
processor.export_to_csv("output.csv")
processor.export_to_excel("output.xlsx")

# Access transaction data
transactions = result['transactions']
statement_info = result['statement_info']
```

## Testing Your Setup

Run the setup checker:
```bash
python setup_veryfi.py
```

This will verify:
- ✅ Python version compatibility
- ✅ Dependencies installed
- ✅ Veryfi credentials configured
- ✅ Output directories created

## Troubleshooting

1. **Import Errors**: Make sure virtual environment is activated
2. **Credential Errors**: Verify your Veryfi API keys are correct
3. **File Not Found**: Check PDF path is correct
4. **Permission Errors**: Ensure write access to output directory

## Cost Estimate

Veryfi pricing (approximate):
- **Free tier**: Limited documents per month
- **Paid plans**: ~$0.10-0.50 per document
- **Bank statements**: Typically 1-3 pages = 1 API call

Your Wells Fargo statement at:
`D:\Development\GnS\Bank_Categorization\input\WellsFargo\bankStatement\_013125 WellsFargo.pdf`
will be processed automatically when you run the script.
