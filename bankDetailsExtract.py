import os
import re
import pdfplumber
import pandas as pd
from decimal import Decimal
from dateutil import parser as dateparser
from pathlib import Path


# ==================================================
# Helpers
# ==================================================
def clean_amount(s):
    """Convert string to Decimal, handle negatives, commas, $."""
    if not s:
        return None
    s = str(s).replace("$", "").replace(",", "").replace("−", "-").strip()
    if not s:
        return None
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    try:
        val = Decimal(s)
    except Exception:
        return None
    if negative or val < 0:
        return -abs(val)
    return val


def try_parse_date(s):
    """Try to convert string into YYYY-MM-DD date."""
    if not s:
        return None
    try:
        return dateparser.parse(s, fuzzy=True, dayfirst=False).date().isoformat()
    except Exception:
        return None


def detect_bank(text):
    """Detect bank name based on keywords in text."""
    text_upper = text.upper()
    if "WELLS FARGO" in text_upper:
        return "Wells Fargo"
    if "BMO" in text_upper:
        return "BMO"
    if "CHASE" in text_upper:
        return "Chase"
    if "CREDIT CARD STATEMENT" in text_upper:
        return "Credit Card"
    return "Unknown"


# ==================================================
# Specialized Wells Fargo Parser (sample3)
# ==================================================
def parse_wellsfargo(pdf_path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table:
                # Skip headers or empty rows
                if not row or "Date" in row[0] or "Transaction" in row[0]:
                    continue

                date, number, desc, credit, debit, balance = None, None, None, None, None, None

                if len(row) >= 6:
                    date, number, desc, credit, debit, balance = row[:6]
                elif len(row) == 5:
                    date, number, desc, credit, debit = row
                elif len(row) == 4:
                    date, desc, credit, debit = row

                rows.append({
                    "date": try_parse_date(date),
                    "number": number.strip() if number else None,
                    "description": desc.strip() if desc else None,
                    "credit": clean_amount(credit),
                    "debit": clean_amount(debit),
                    "balance": clean_amount(balance)
                })
    return pd.DataFrame(rows)


# ==================================================
# Universal extractor (robust)
# ==================================================
def extract_transactions(pdf_path):
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # --- Step 1: Extract words with positions
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue

            # --- Step 2: Group words by line (y0 coordinate, rounded)
            rows = {}
            for w in words:
                y = round(w["top"], 1)
                if y not in rows:
                    rows[y] = []
                rows[y].append(w)

            # --- Step 3: Sort rows by vertical position, words by x
            for y in sorted(rows.keys()):
                row = sorted(rows[y], key=lambda x: x["x0"])
                line = " ".join(w["text"] for w in row)

                # --- Step 4: Try parsing as transaction
                m = re.match(r"^(\d{2}/\d{2}|[A-Za-z]{3}\s+\d{1,2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})$", line)
                if m:
                    date_s, desc, amt = m.groups()
                    amt_val = clean_amount(amt)
                    debit, credit = (abs(amt_val), None) if amt_val < 0 else (None, amt_val)
                    results.append({
                        "date": try_parse_date(date_s),
                        "description": desc.strip(),
                        "debit": debit,
                        "credit": credit,
                        "balance": None,
                        "raw": line
                    })
                else:
                    # --- Step 5: If no amount found, append line to last description
                    if results:
                        results[-1]["description"] += " " + line
                        results[-1]["raw"] += " | " + line

    return results


# ==================================================
# Unified parser
# ==================================================
def parse_statement(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([p.extract_text() or "" for p in pdf.pages])

    bank = detect_bank(text)

    # Specialized Wells Fargo parser
    if bank == "Wells Fargo" and "TRANSACTION HISTORY" in text.upper():
        rows = parse_wellsfargo(text)
    else:
        # Universal extractor for all other cases
        rows = extract_transactions(pdf_path)

    # Add bank name to each row
    for r in rows:
        r["bank"] = bank

    return pd.DataFrame(rows)


# ==================================================
# Batch Processor
# ==================================================
BASE_DIR = Path(__file__).parent.resolve()
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def process_pdfs():
    pdf_files = list(INPUT_DIR.glob("*.pdf")) + list(INPUT_DIR.glob("*.PDF"))
    if not pdf_files:
        print(f"⚠️ No PDF files found in {INPUT_DIR}")
        return

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        df = parse_statement(pdf_file)

        if df.empty:
            print(f"⚠️ No transactions found in {pdf_file.name}")
            continue

        output_file = OUTPUT_DIR / f"{pdf_file.stem}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"✅ Saved: {output_file}")


if __name__ == "__main__":
    process_pdfs()
