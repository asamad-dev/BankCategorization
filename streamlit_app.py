import streamlit as st
import os
import pandas as pd
import subprocess
from pdfextraction.bankDetailsExtract import parse_statement

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
            st.info("Running categorization (main.py)...")
            result = subprocess.run(
                ["python3", "main.py"],
                capture_output=True,
                text=True
            )
            st.write("Categorization Output:")
            st.code(result.stdout)
            if result.stderr:
                st.error(result.stderr)
    else:
        st.error("No transactions found in this PDF.")