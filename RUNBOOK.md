# Bank Categorization Project - Streamlit App Runbook

## Prerequisites

1. **Python**: Ensure Python 3.8+ is installed
2. **Virtual Environment**: Recommended to use a virtual environment

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
git clone <repository-url>
cd Bank_Categorization
```

### 2. Create Virtual Environment
```bash
# Try python first, if not available use python3 or py
python -m venv venv
# OR if python command not found:
python3 -m venv venv
# OR on Windows:
py -m venv venv
```

### 3. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
# If you're in the virtual environment:
pip install -r requirements.txt

# If pip is not found, try:
python -m pip install -r requirements.txt
# OR
python3 -m pip install -r requirements.txt
# OR on Windows:
py -m pip install -r requirements.txt
```

### 5. Environment Variables Setup ⚠️ **CRITICAL STEP**
Create a `.env` file in the project root with the following variables:

**Create file:** `.env` (in the same directory as `streamlit_app.py`)

```env
# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
index_name=banktransactions

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# Embedding Model
emb_model=sentence-transformers/all-MiniLM-L6-v2

# Server Configuration (optional)
HOST=0.0.0.0
PORT=8000
CORS_ALLOWED_ORIGINS=*
```

**⚠️ IMPORTANT**: Replace `your_pinecone_api_key_here` and `your_google_api_key_here` with your actual API keys!

## Running the Application

### Start Streamlit App
```bash
streamlit run streamlit_app.py
```

The app will be available at: `http://localhost:8501`

### Alternative: Start FastAPI Backend
```bash
# Try python first, if not available use python3 or py
python main.py
# OR if python command not found:
python3 main.py
# OR on Windows:
py main.py
```

The API will be available at: `http://localhost:8000`

## Usage

1. **Upload PDF**: Use the file uploader to select a bank statement PDF
2. **Extract Transactions**: The app will automatically parse the PDF and extract transactions
3. **Download Excel**: Download the extracted transactions as an Excel file
4. **Categorize**: Click the "Categorize" button to run transaction categorization using AI
   - ✅ **Fast**: Direct function call (no subprocess overhead)
   - ✅ **Reliable**: No timeout issues
   - ✅ **Better Error Handling**: Clear feedback on missing API keys

## Supported Banks

- Wells Fargo (Business Checking & Credit Cards)
- BMO (Business Checking & Credit Cards)
- Chase (Credit Cards)
- Bank of America (Business Banking)
- JPMorgan Chase Bank

## Troubleshooting

### Common Issues:

1. **Python Command Not Found**: 
   - **Windows**: Install Python from Microsoft Store or python.org (ensure "Add to PATH" is checked)
   - **Try different commands**: `python`, `python3`, or `py`
   - **Alternative**: Use `py -m pip install -r requirements.txt` on Windows

2. **Missing API Keys**: 
   - ⚠️ **CRITICAL**: Ensure all required API keys are set in the `.env` file
   - The app will show debugging info if keys are missing
   - Check the "🔍 Debugging Information" section when categorization fails

3. **PDF Upload Fails**: Check that the PDF is a valid bank statement format

4. **Categorization Errors**: 
   - Verify Pinecone and Google API credentials in `.env` file
   - Check network connectivity
   - The app now provides detailed error information

5. **Port Already in Use**: Change the PORT in `.env` or kill existing processes

### Logs
Check `centrix.log` for detailed application logs and error messages.

## Project Structure

```
Bank_Categorization/
├── streamlit_app.py          # Main Streamlit application
├── main.py                   # FastAPI backend
├── requirements.txt          # Python dependencies
├── pdfextraction/           # PDF parsing modules
├── backend/                 # Backend services
│   ├── routes/              # API routes
│   ├── services/            # Business logic
│   ├── interactors/         # Data processing
│   └── utils/               # Utilities
├── input/                   # PDF upload directory
└── output/                  # Processed files directory
```

## API Endpoints

- `POST /api/Add_GL_in_vecdb_pipeline` - Add documents to vector database
- `POST /api/get_category` - Get transaction categorization

For more details, visit `http://localhost:8000/docs` when the FastAPI server is running.
