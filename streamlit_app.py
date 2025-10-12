import streamlit as st
import os
import pandas as pd
import asyncio
import csv
from io import StringIO
from pdfextraction.bankDetailsExtract import parse_statement
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import categorization function
try:
    from backend.interactors.transaction import call as categorize_transactions
except ImportError as e:
    st.error(f"Error importing categorization function: {e}")
    categorize_transactions = None

st.title("Bank Statement PDF to Excel Converter")

input_folder = "input"
output_folder = "output"
os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

uploaded_file = st.file_uploader("Upload a PDF bank statement", type=["pdf"])

if uploaded_file is not None:
    pdf_file_path = os.path.join(input_folder, uploaded_file.name)
    with open(pdf_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Uploaded {uploaded_file.name} to {input_folder}")

    # Extract transactions
    df = parse_statement(pdf_file_path)
    if not df.empty:
        st.write("Extracted Transactions:")
        st.dataframe(df)
        excel_file_name = uploaded_file.name.replace(".pdf", ".xlsx")
        excel_file_path = os.path.join(output_folder, excel_file_name)
        df.to_excel(excel_file_path, index=False)
        with open(excel_file_path, "rb") as excel_file:
            st.download_button(
                label="Download Excel",
                data=excel_file,
                file_name=excel_file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        # Add Categorize button
        if st.button("Categorize"):
            if categorize_transactions is None:
                st.error("❌ Categorization function not available. Check your environment setup.")
            else:
                st.info("🔄 Running categorization...")
                
                # Convert DataFrame to CSV format for the categorization function
                csv_buffer = StringIO()
                df.to_csv(csv_buffer, index=False)
                csv_content = csv_buffer.getvalue().encode('utf-8')
                
                # Create a file-like object for the categorization function
                class FileWrapper:
                    def __init__(self, content):
                        self.content = content
                        
                    async def read(self):
                        return self.content
                
                file_wrapper = FileWrapper(csv_content)
                
                try:
                    # Run the categorization function directly
                    with st.spinner("Categorizing transactions..."):
                        result = asyncio.run(categorize_transactions(file_wrapper))
                    
                    st.success("✅ Categorization completed!")
                    st.write("**Categorization Result:**")
                    st.code(str(result))
                    
                    # Check if a categorized file was created
                    categorized_file = "_022924 WellsFargo.xlsx - Sheet1.csv"
                    if os.path.exists(categorized_file):
                        st.success(f"📄 Categorized file created: {categorized_file}")
                        
                        # Try to read and display the categorized data
                        try:
                            categorized_df = pd.read_csv(categorized_file)
                            st.write("**Categorized Transactions Preview:**")
                            st.dataframe(categorized_df.head())
                            
                            # Provide download link
                            with open(categorized_file, "rb") as f:
                                st.download_button(
                                    label="📥 Download Categorized CSV",
                                    data=f.read(),
                                    file_name=f"categorized_{uploaded_file.name.replace('.pdf', '.csv')}",
                                    mime="text/csv"
                                )
                        except Exception as e:
                            st.warning(f"Could not preview categorized file: {e}")
                            
                except Exception as e:
                    st.error(f"❌ Categorization failed: {str(e)}")
                    st.error("This might be due to missing API keys or network issues.")
                    
                    # Show helpful debug info
                    with st.expander("🔍 Debugging Information"):
                        st.write("**Environment Variables Check:**")
                        st.write(f"- PINECONE_API_KEY: {'✅ Set' if os.getenv('PINECONE_API_KEY') else '❌ Missing'}")
                        st.write(f"- GOOGLE_API_KEY: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Missing'}")
                        st.write(f"- emb_model: {os.getenv('emb_model', 'Not set')}")
                        st.write(f"**Error Details:** {str(e)}")
    else:
        st.error("No transactions found in this PDF.")