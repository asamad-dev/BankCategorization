
# from backend.services.pinecone import create_vector_db
# from backend.utils.logger import log_message
# from langchain_core.documents import Document
# import csv,io,os
# from io import StringIO
# from typing import List, Dict
# from backend.services.pinecone import retrieve_documents, load_vectordb
# from backend.utils.embed import huggingface_emb
# from langchain_google_genai import ChatGoogleGenerativeAI

# embeddings = huggingface_emb()
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
#     api_key = os.getenv("GOOGLE_API_KEY")
# )


# def clean_and_rename_data(data: List[Dict]) -> List[Dict]:
#     """
#     Transforms the list of dictionaries to exclude 'Unnamed: 2' 
#     and rename 'Unnamed: 1' to 'category' and 'Memo' to 'page_content'.
#     """
#     cleaned_data = []
    
#     for row in data:
#         # Create a new dictionary for the transformed row
#         new_row = {}
        
#         # 1. Rename 'Unnamed: 1' to 'category'
#         if 'Unnamed: 1' in row:
#             new_row['category'] = row['Unnamed: 1']
            
#         # 2. Rename 'Memo' to 'page_content'
#         if 'Memo' in row:
#             new_row['page_content'] = row['Memo']
            
#         # 3. 'Unnamed: 2' is intentionally excluded
        
#         cleaned_data.append(new_row)
        
#     return cleaned_data


# async def add_doc_call(file):
#     # create pipeline to add transaction data in pinecone index
#     #preprocessing step for fetching trasaction from document and pass it in document form
#     try:
#         content = await file.read()
#         decoded = content.decode("utf-8")
#         string_io = StringIO(decoded)
#         reader = csv.DictReader(string_io)
#         all_rows = list(reader)
#         cleaned_data = clean_and_rename_data(all_rows)
#         documents = [Document(page_content=row['page_content'], metadata={'category': row['category']}) for row in cleaned_data if 'page_content' in row and 'category' in row]
        
#         log_message("info","doc fetching successful")
#     except Exception as e:
#         log_message("error","doc fetching was unsuccessful")


#     try:
#         add_documents = create_vector_db(documents)
#         log_message("info","document added to db")
#         return add_documents
#     except Exception as e:
#         log_message ("error","doc was not added to index")



#     return "Documents Successfully Addded to Vector DB"




# def predict_category(description: str) -> str:
#     vector_store = load_vectordb(index_name="banktransactions", embeddings=embeddings)
#     page_contents = retrieve_documents(vector_store, description)
#     llm_answer = llm.invoke(f"check the provided categories in data and see if its relevant to provided tansaction if yes oreturn the category only if no return unknown. Transaction description: {description}. Categories: {page_contents}")
#     return llm_answer.content

# def predict_llm_category(description):
#     llm_category = llm.invoke(f"Predict the category for provided bank transaction of a company according to US Tax Forms, If the transaction contains something you need to ask from client return unknown otherwise just return the category. Transaction description : {description}")
#     return llm_category
# def predict_COA_category(description):
#     accounts = [
#     "Wells Fargo #7832",
#     "Accounts Receivable",
#     "Advance against Purchases",
#     "Driver Advances",
#     "Factoring Cash Reserve",
#     "Factoring Escrow Reserve",
#     "Factoring Triumph Receivables",
#     "Investment Savings",
#     "Loan - Dalbir Singh",
#     "Loan to JKP Logistics",
#     "Loan to JKP Logistics Inc",
#     "Loan to Milestone Logistics",
#     "Prepaid Insurance",
#     "Security Deposit",
#     "Accumulated Depreciation",
#     "Furniture and Equipment",
#     "Other Fixed Assets",
#     "Tractors and Trailers",
#     "Truck & Trailers",
#     "Loan to Jobanjeet Singh",
#     "Loan to Shareholder",
#     "Accounts Payable",
#     "Factoring Triumph Liability",
#     "Loan from Elite Cargo",
#     "Loan to Balkar Singh",
#     "Loan to Roadhawk",
#     "OCL",
#     "Payroll Liabilities",
#     "Unapplied Loan Payments",
#     "Long Term Liability",
#     "Long Term Liability:CITI Bank Loan",
#     "Long Term Liability:COMMERCIAL CREDIT GROUP",
#     "Long Term Liability:GOTOPREMIUMFINANCE.COM LLC",
#     "Long Term Liability:TBK Bank",
#     "Long Term Liability:UMPQUA BANK",
#     "Long Term Liability:Wallwork",
#     "Wallwork Loan $8128.32 #18364-1",
#     "Capital Stock",
#     "Opening Balance Equity",
#     "Owner's draw",
#     "Retained Earnings",
#     "Shareholder Distributions",
#     "Fuel Surcharge",
#     "Gross Trucking Income",
#     "Driver Pay",
#     "Fuel for Hired Vehicles",
#     "Liability Insurance",
#     "Subhaulers & Carriers",
#     "Travel Expenses for Drivers",
#     "Truck Maintenance Costs",
#     "Advertisement Expense",
#     "Automobile Expense",
#     "Bank Service Charges",
#     "Business License and Permits",
#     "Business Licenses and Permits",
#     "Computer and Internet Expenses",
#     "Contractor Expenses",
#     "Depreciation Expense",
#     "Drug Testing",
#     "Dues & Subscription",
#     "Equipment Lease",
#     "Factoring Fees",
#     "Fine and Penalties",
#     "Insurance Expense",
#     "Interest Expense",
#     "Meals and Entertainment",
#     "Office Expense",
#     "Office Supplies",
#     "Payroll Expenses",
#     "Payroll Expenses:Payroll Taxes",
#     "Payroll Expenses:Payroll Wages",
#     "Professional Fees",
#     "Rent Expense",
#     "Repairs and Maintenance",
#     "Small Tools and Equipment",
#     "Taxes",
#     "Telephone Expense",
#     "Tolls and Parking",
#     "Travel Expense",
#     "Utilities",
#     "Yard Rent",
#     "Ask My Accountant"
# ]
#     coa_category = llm.invoke(f"Get category from Buisness COA and return it for the provided transaction. Transactions description : {description}, COA_list : {accounts} ")
#     return coa_category



# def call(file):
#     # create pipeline to get category of transaction from pinecone index
#     try:
#         content = file.file.read()
#         decoded = content.decode("utf-8")
#         string_io = StringIO(decoded)
#         reader = csv.DictReader(string_io)
#         all_rows = list(reader)
#         for row in all_rows:
#             row["GL_category"] = predict_category(row["description"])
#             row["LLM_category"] = predict_llm_category(row["description"])
#             row["COA_category"] = predict_COA_category(row["description"])
#         output_path = os.path.join(os.getcwd(), "categorized_transaction.csv")
#         with open(output_path, "w", newline="", encoding="utf-8") as f:
#             writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
#             writer.writeheader()
#             writer.writerows(all_rows)

#     # print(f"✅ Saved categorized CSV: {output_path}")

#         return f"✅ Saved categorized CSV: {output_path}"
#     except Exception as e:
#         log_message ("error","doc was not fetched from index")


import os
import csv
import io
import asyncio
from io import StringIO
from typing import List, Dict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.services.pinecone import (
    create_vector_db,
    retrieve_documents,
    load_vectordb
)
from backend.utils.logger import log_message
from backend.utils.embed import huggingface_emb


# ========== GLOBAL INITIALIZATION ==========
embeddings = huggingface_emb()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=os.getenv("GOOGLE_API_KEY")
)


# ========== DATA CLEANING ==========

def clean_and_rename_data(data: List[Dict]) -> List[Dict]:
    """Clean and rename columns for consistency."""
    cleaned = []
    for row in data:
        new_row = {}
        if 'Unnamed: 1' in row:
            new_row['category'] = row['Unnamed: 1']
        if 'Memo' in row:
            new_row['page_content'] = row['Memo']
        if new_row:
            cleaned.append(new_row)
    return cleaned


# ========== DOCUMENT ADDITION PIPELINE ==========

async def add_doc_call(file):
    """Async pipeline to add transaction data into Pinecone index."""
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.DictReader(StringIO(decoded))
        cleaned_data = clean_and_rename_data(list(reader))

        documents = [
            Document(
                page_content=row["page_content"],
                metadata={"category": row["category"]}
            )
            for row in cleaned_data if "page_content" in row and "category" in row
        ]

        log_message("info", "Document fetching successful")
    except Exception as e:
        log_message("error", f"Doc fetching failed: {e}")
        return {"status": "failed", "error": str(e)}

    try:
        await asyncio.to_thread(create_vector_db, documents)
        log_message("info", "Documents added to Pinecone")
        return {"status": "success", "count": len(documents)}
    except Exception as e:
        log_message("error", f"Vector DB addition failed: {e}")
        return {"status": "failed", "error": str(e)}


# ========== CATEGORY PREDICTION HELPERS ==========

async def predict_category(description: str) -> str:
    """Predict category from Pinecone vector store."""
    try:
        vector_store = await asyncio.to_thread(load_vectordb, index_name="banktransactions", embeddings=embeddings)
        page_contents = await asyncio.to_thread(retrieve_documents, vector_store, description)
        prompt = (
            f"""Check provided categories and return category if relevant, otherwise 'unknown'.Response Guidlines : 1. You must return with the category or if not predited must return unknown, 2. You must not provide any other instructions or details. "
            Transaction: {description}. Categories: {page_contents}"""
        )
        llm_answer = await asyncio.to_thread(llm.invoke, prompt)
        return llm_answer.content.strip()
    except Exception:
        return "unknown"


async def predict_llm_category(description: str) -> str:
    """LLM-based standalone US-tax-form category prediction."""
    prompt = (
        f"""Predict the category for this bank transaction per US Tax Forms. "
        If uncertain, return 'unknown'.Response Guidlines : 1. You must return with the category or if not predited must return unknown, 2. You must not provide any other instructions or details. Transaction: {description}"""
    )
    try:
        llm_answer = await asyncio.to_thread(llm.invoke, prompt)
        return llm_answer.content.strip()
    except Exception:
        return "unknown"


async def predict_COA_category(description: str) -> str:
    """Predict category from fixed COA list."""
    accounts = [
        "Wells Fargo #7832", "Accounts Receivable", "Advance against Purchases",
        "Driver Advances", "Factoring Cash Reserve", "Factoring Escrow Reserve",
        "Factoring Triumph Receivables", "Investment Savings", "Loan - Dalbir Singh",
        "Loan to JKP Logistics", "Loan to JKP Logistics Inc", "Loan to Milestone Logistics",
        "Prepaid Insurance", "Security Deposit", "Accumulated Depreciation",
        "Furniture and Equipment", "Other Fixed Assets", "Tractors and Trailers",
        "Truck & Trailers", "Loan to Jobanjeet Singh", "Loan to Shareholder",
        "Accounts Payable", "Factoring Triumph Liability", "Loan from Elite Cargo",
        "Loan to Balkar Singh", "Loan to Roadhawk", "OCL", "Payroll Liabilities",
        "Unapplied Loan Payments", "Long Term Liability", "Capital Stock",
        "Opening Balance Equity", "Owner's draw", "Retained Earnings",
        "Shareholder Distributions", "Fuel Surcharge", "Gross Trucking Income",
        "Driver Pay", "Fuel for Hired Vehicles", "Liability Insurance",
        "Subhaulers & Carriers", "Travel Expenses for Drivers", "Truck Maintenance Costs",
        "Advertisement Expense", "Automobile Expense", "Bank Service Charges",
        "Business Licenses and Permits", "Computer and Internet Expenses",
        "Contractor Expenses", "Depreciation Expense", "Drug Testing", "Dues & Subscription",
        "Equipment Lease", "Factoring Fees", "Fine and Penalties", "Insurance Expense",
        "Interest Expense", "Meals and Entertainment", "Office Expense",
        "Office Supplies", "Payroll Expenses", "Payroll Expenses:Payroll Taxes",
        "Payroll Expenses:Payroll Wages", "Professional Fees", "Rent Expense",
        "Repairs and Maintenance", "Small Tools and Equipment", "Taxes",
        "Telephone Expense", "Tolls and Parking", "Travel Expense", "Utilities",
        "Yard Rent", "Ask My Accountant"
    ]

    prompt = f"Get category from Business COA for transaction. Response Guidlines : 1. You must return with the category or if not predited must return unknown, 2. You must not provide any other instructions or details. Transaction: {description}. COA list: {accounts}"
    try:
        llm_answer = await asyncio.to_thread(llm.invoke, prompt)
        return llm_answer.content.strip()
    except Exception:
        return "unknown"


# ========== MAIN PIPELINE ==========

async def call(file):
    """Parallelized categorization of transactions using all predictors."""
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        reader = csv.DictReader(StringIO(decoded))
        rows = list(reader)

        async def process_row(row):
            desc = row["description"]
            results = await asyncio.gather(
                predict_category(desc),
                predict_llm_category(desc),
                predict_COA_category(desc)
            )
            row["GL_category"], row["LLM_category"], row["COA_category"] = results
            return row

        # Process all rows concurrently
        categorized_rows = await asyncio.gather(*(process_row(r) for r in rows))

        output_path = os.path.join(os.getcwd(), "_022924 WellsFargo.xlsx - Sheet1.csv")
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=categorized_rows[0].keys())
            writer.writeheader()
            writer.writerows(categorized_rows)

        return f"✅ Saved categorized CSV: {output_path}"

    except Exception as e:
        log_message("error", f"Categorization failed: {e}")
        return {"status": "failed", "error": str(e)}

