import os
import re
import pdfplumber
import pandas as pd
from decimal import Decimal
from dateutil import parser as dateparser
from pathlib import Path
import re


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
    if not text:
        return "Unknown"
    text_upper = text.upper().replace("\u00A0", " ")

    if "WELLS FARGO" in text_upper:
        return "Wells Fargo"
    if "BMO" in text_upper:   # ✅ catch BMO Harris/Bank
        return "BMO"
    if "JPMORGAN CHASE BANK" in text_upper or "CHASE BANK" in text_upper:
        return "Chase Bank"
    if "BANK OF AMERICA" in text_upper: #Bank of amrica check
        return "Bank of America"
    if "CHASE" in text_upper and "CREDIT CARD STATEMENT" in text_upper:
        return "Chase Credit Card"
    if "CREDIT CARD STATEMENT" in text_upper:
        return "Credit Card"
    return "Unknown"


# ==================================================
# Specialized Wells Fargo Parser
# ==================================================

#Parse Wells Fargo business statements Start
def parse_wellsfargo(pdf_path):
    """Parse Wells Fargo business statements into one row: date, desc, debit, credit, balance."""
    rows = []
    date_re = re.compile(r"^\d{1,2}/\d{1,2}\b")

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for line in text.split("\n"):
                line = line.strip()
                if not line or line.startswith(("Date", "Transaction", "Check Deposits", "Accountnumber")):
                    continue

                if date_re.match(line):
                    parts = line.split()
                    date_s = parts[0]
                    rest = " ".join(parts[1:])

                    # Extract amounts
                    amounts = re.findall(r"\d[\d,]*\.\d{2}", rest)
                    debit = credit = balance = None

                    if amounts:
                        if len(amounts) == 1:
                            amt = clean_amount(amounts[0])
                            # Heuristic: credit vs debit
                            if "Deposit" in rest or "Credit" in rest:
                                credit = amt
                            else:
                                debit = amt
                        elif len(amounts) == 2:
                            # Usually credit + balance
                            credit = clean_amount(amounts[0])
                            balance = clean_amount(amounts[1])
                        elif len(amounts) == 3:
                            # Debit, credit, balance all present
                            debit = clean_amount(amounts[0])
                            credit = clean_amount(amounts[1])
                            balance = clean_amount(amounts[2])

                        # Remove numbers → leave description only
                        desc = re.sub(r"\d[\d,]*\.\d{2}", "", rest).replace("<", "").strip()
                    else:
                        desc = rest

                    rows.append({
                        "date": try_parse_date(date_s),
                        "description": desc,
                        "debit": debit,
                        "credit": credit,
                        "balance": balance
                    })

                else:
                    # continuation line → append to last row description
                    if rows:
                        rows[-1]["description"] += " " + line

    return rows

#Parse Wells Fargo business statements End

#For chase bank credit card statements

def parse_chase_credit(pdf_path):
    """Parse Chase credit card statement transactions."""
    rows = []
    txn_pattern = re.compile(r"^(\d{2}/\d{2})\s+(.+?)\s+(-?[\d,]+\.\d{2})$")

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split("\n"):
                m = txn_pattern.match(line)
                if m:
                    date, desc, amount = m.groups()
                    amt = clean_amount(amount)
                    debit, credit = (abs(amt), None) if amt < 0 else (None, amt)

                    rows.append({
                        "date": try_parse_date(date),
                        "description": desc.strip(),
                        "debit": debit,
                        "credit": credit,
                        "balance": None
                    })
                else:
                    # Append continuation lines to last transaction description
                    if rows:
                        rows[-1]["description"] += " " + line.strip()
    return rows

#BMO bank is correct handle both old and new categryries
#Old style like Sample9

def parse_bmo_old(pdf_path):
    """
    Parse BMO Business Checking (Old Style like sample9).
    Sections:
      - Deposits and Other Credits  (Date Amount Description)
      - Withdrawals and Other Debits (Date Amount Description)
      - Daily Balance Summary (two columns of Date Balance pairs)
    Output rows: {date, description, debit, credit, balance}
    """
    rows = []
    section = None
    statement_year = None

    # Helpers
    MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"

    def date_with_year(mon, day):
        # Use year from "Statement Period ... TO ..." (first page)
        if statement_year:
            return f"{mon} {int(day)} {statement_year}"
        return f"{mon} {int(day)}"  # fallback

    with pdfplumber.open(pdf_path) as pdf:
        # ---- Get the statement year from page 1, e.g. "Statement Period 04/01/25 TO 04/30/25"
        first_text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
        m_yr = re.search(r"Statement\s+Period\s+\d{2}/\d{2}/(\d{2,4})\s+TO\s+\d{2}/\d{2}/(\d{2,4})", first_text, re.I)
        if m_yr:
            y = m_yr.group(2)
            y = f"20{y}" if len(y) == 2 else y
            try:
                statement_year = int(y)
            except:
                statement_year = None

        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw_line in text.split("\n"):
                line = raw_line.strip()
                if not line:
                    continue

                # ---- Section switches
                if re.search(r"Deposits\s+and\s+other\s+credits", line, re.I):
                    section = "deposits"
                    continue
                if re.search(r"Withdrawals\s+and\s+other\s+debits", line, re.I):
                    section = "withdrawals"
                    continue
                if re.search(r"(Daily\s+Balance\s+Summary|Daily\s+ledger\s+balances)", line, re.I):
                    section = "balances"
                    continue

                # ---- Skip obvious headers / totals / boilerplate
                if re.search(r"^Date\s+Amount\s+Description", line, re.I):
                    continue
                if re.search(r"(Total deposits|Total withdrawals|Service fee|Statement Period Rates|DEPOSIT ACCOUNT SUMMARY)", line, re.I):
                    continue
                if re.fullmatch(r"Interest Paid(?:.*)?", line, re.I):
                    # handled by the Deposits section row itself when it appears with a date
                    continue

                # ---- Deposits / Withdrawals: "Mon DD  Amount  Description"
                if section in ("deposits", "withdrawals"):
                    m = re.match(
                        rf"^{MONTH}\s+(\d{{1,2}})\s+(\(?-?\$?[\d,]*\.\d{{2}}\)?|\.\d{{2}})\s+(.*)$",
                        line
                    )
                    if m:
                        mon, day, amt_s, desc = m.group(1), m.group(2), m.group(3), m.group(4)
                        amt = clean_amount(amt_s)  # preserves sign/parentheses exactly
                        rows.append({
                            "date": try_parse_date(date_with_year(mon, day)),
                            "description": desc.strip(),
                            "debit": amt if section == "withdrawals" else None,
                            "credit": amt if section == "deposits" else None,
                            "balance": None
                        })
                    else:
                        # wrapped description line → append to last transaction
                        if rows:
                            rows[-1]["description"] = (rows[-1]["description"] + " " + line).strip()
                    continue

                # ---- Daily Balance Summary: each line has up to TWO "Mon DD Amount" pairs
                if section == "balances":
                    # find all "Mon DD Amount" triples on the line
                    triples = list(re.finditer(
                        rf"{MONTH}\s+(\d{{1,2}})\s+(\(?-?\$?[\d,]*\.\d{{2}}\)?|\.\d{{2}})",
                        line
                    ))
                    for t in triples:
                        mon = t.group(1)
                        day = t.group(2)
                        bal_s = t.group(3)
                        rows.append({
                            "date": try_parse_date(date_with_year(mon, day)),
                            "description": "Daily Balance",
                            "debit": None,
                            "credit": None,
                            "balance": clean_amount(bal_s)
                        })
                    continue

                # Fallback: continuation line for any previous row
                if rows:
                    rows[-1]["description"] = (rows[-1]["description"] + " " + line).strip()

    return rows

#New style like Sample10
#Helper functions inside
def _bmo_clean_amount_exact(s: str):
    """Parse amount exactly as shown; keep sign/parentheses."""
    if not s:
        return None
    s = str(s).strip().replace(",", "").replace("$", "")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = s.replace("+", "")
    try:
        val = Decimal(s)
    except Exception:
        m = re.search(r"-?\d+(?:\.\d{1,2})?", s)
        if not m:
            return None
        try:
            val = Decimal(m.group(0))
        except Exception:
            return None
    return -val if neg else val
def _bmo_find_header(words):
    """Find the y of the header line and the header words on that line."""
    rows = {}
    for w in words:
        y = round(w["top"], 1)
        rows.setdefault(y, []).append(w)

    for y in sorted(rows.keys()):
        line = " ".join(w["text"] for w in sorted(rows[y], key=lambda ww: ww["x0"])).lower()
        if ("date" in line and "description" in line and "withdraw" in line
            and "deposit" in line and "balance" in line):
            return y, sorted(rows[y], key=lambda ww: ww["x0"])
    return None, []
def _bmo_header_centers(header_words):
    """Map canonical columns to their x-centers, using the header words."""
    centers = {}
    for w in header_words:
        t = w["text"].strip().lower()
        cx = (w["x0"] + w["x1"]) / 2.0
        if t == "date" and "date" not in centers:
            centers["date"] = cx
        elif "withdraw" in t and "withdrawal" not in centers:
            centers["withdrawal"] = cx
        elif "deposit" in t and "deposit" not in centers:
            centers["deposit"] = cx
        elif "balance" in t and "balance" not in centers:
            centers["balance"] = cx
        elif "description" in t and "description" not in centers:
            centers["description"] = cx
        elif t == "transaction" and "description" not in centers:
            centers["description"] = cx  # header may read "Transaction description"

    # If description is missing, estimate it mid-way between date and withdrawal
    if "description" not in centers and "date" in centers and "withdrawal" in centers:
        centers["description"] = (centers["date"] + centers["withdrawal"]) / 2.0
    return centers
def _bmo_edges_from_centers(centers, xmin, xmax):
    """Build left/right spans for each column from header centers."""
    items = sorted(centers.items(), key=lambda kv: kv[1])
    spans = []
    for i, (name, cx) in enumerate(items):
        left = xmin if i == 0 else (items[i-1][1] + cx) / 2.0
        right = xmax if i == len(items)-1 else (cx + items[i+1][1]) / 2.0
        spans.append((name, left, right))
    return spans
def _bmo_pick_col(xc, spans):
    for name, left, right in spans:
        if left <= xc <= right:
            return name
    return None
#Helper End For BMO
def parse_bmo_new(pdf_path):
    """
    STRICT parser for BMO Business Checking (Sample10-style).
    Columns are taken *exactly* as in the PDF:
      Withdrawal -> debit,  Deposit -> credit,  Balance -> balance.
    Signs are preserved exactly (no abs(), no remapping).
    Wrapped description lines get appended to the previous row.
    """
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                x_tolerance=1.5, y_tolerance=2.0,
                keep_blank_chars=False, use_text_flow=True
            )
            if not words:
                continue

            header_top, header_words = _bmo_find_header(words)
            if header_top is None:
                continue

            centers = _bmo_header_centers(header_words)
            # Must have at least these; description is inferred if missing
            if not {"date", "withdrawal", "deposit", "balance"}.issubset(centers.keys()):
                continue

            xmin = min(w["x0"] for w in words)
            xmax = max(w["x1"] for w in words)
            spans = _bmo_edges_from_centers(centers, xmin, xmax)

            # Group words by row below the header
            line_map = {}
            for w in words:
                if w["top"] <= header_top:
                    continue
                y = round(w["top"], 1)
                line_map.setdefault(y, []).append(w)

            for y in sorted(line_map):
                rwords = sorted(line_map[y], key=lambda ww: ww["x0"])
                cols = {"date": [], "description": [], "withdrawal": [], "deposit": [], "balance": []}
                for w in rwords:
                    col = _bmo_pick_col((w["x0"] + w["x1"]) / 2.0, spans)
                    if not col:
                        continue
                    t = w["text"]
                    if t.lower().startswith("page "):
                        continue
                    cols.setdefault(col, []).append(t)

                date_txt = " ".join(cols.get("date", [])).strip()
                desc_txt = " ".join(cols.get("description", [])).strip()
                w_txt    = " ".join(cols.get("withdrawal", [])).strip()
                d_txt    = " ".join(cols.get("deposit", [])).strip()
                b_txt    = " ".join(cols.get("balance", [])).strip()

                # Skip empty lines
                if not any([date_txt, desc_txt, w_txt, d_txt, b_txt]):
                    continue

                # Wrapped description line (no date/amounts): append to previous
                if (not date_txt) and (not w_txt) and (not d_txt) and (not b_txt) and desc_txt:
                    if rows:
                        rows[-1]["description"] = (rows[-1]["description"] + " " + desc_txt).strip()
                    continue

                debit   = _bmo_clean_amount_exact(w_txt) if w_txt else None
                credit  = _bmo_clean_amount_exact(d_txt) if d_txt else None
                balance = _bmo_clean_amount_exact(b_txt) if b_txt else None

                rows.append({
                    "date": date_txt or None,  # keep as seen; you can run try_parse_date() later if you want ISO
                    "description": desc_txt,
                    "debit": float(debit) if debit is not None else None,
                    "credit": float(credit) if credit is not None else None,
                    "balance": float(balance) if balance is not None else None,
                })
    return rows

#BMO end 2 categery BMO business also available


#Parse JPMorgan Chase bank statements (sample6/7/8) start
#Helper Functions inside

#Parse JPMorgan Chase bank statements (sample6/7/8) end 


#Bank of Amrica parser start


#Bank of Amrica parser end


# ==================================================
# Universal extractor (for unknown formats)
# ==================================================
def extract_transactions(pdf_path):
    results = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=3, y_tolerance=3)
            if not words:
                continue
            rows = {}
            for w in words:
                y = round(w["top"], 1)
                rows.setdefault(y, []).append(w)
            for y in sorted(rows.keys()):
                row = sorted(rows[y], key=lambda x: x["x0"])
                line = " ".join(w["text"] for w in row)
                m = re.match(r"^(\d{2}/\d{2}|[A-Za-z]{3}\s+\d{1,2})\s+(.+?)\s+(-?\$?[\d,]+\.\d{2})$", line)
                if m:
                    date_s, desc, amt = m.groups()
                    amt_val = clean_amount(amt)
                    debit, credit = (abs(amt_val), None) if amt_val and amt_val < 0 else (None, amt_val)
                    results.append({
                        "date": try_parse_date(date_s),
                        "description": desc.strip(),
                        "debit": debit,
                        "credit": credit,
                        "balance": None,
                        "raw": line
                    })
                else:
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
    print(f"Detected bank: {bank}")
    
    if bank == "Wells Fargo":
        rows = parse_wellsfargo(pdf_path)
    elif bank == "Chase Credit Card":
        rows = parse_chase_credit(pdf_path)
    #elif bank == "Chase Bank":
       # rows = parse_chase_JPMorgan(pdf_path)          # 👈 new Chase checking parser (sample6/7/8)
    elif bank == "Bank of America":   # Bank of amrica parse call   
        rows = parse_bofa(pdf_path)
    elif bank == "BMO":
        # Auto decide old vs new style
        if "Monthly Activity Details" in text:
            rows = parse_bmo_new(pdf_path)   # 👈 new style parser (sample10)
        else:
            rows = parse_bmo_old(pdf_path)   # 👈 old style parser (sample9)
    else:
        rows = extract_transactions(pdf_path)
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
   
