import re
from datetime import datetime

# 1. CLEAN TEXT HELPER
def clean_text(t):
    """Removes non-ASCII characters and trims spaces."""
    return re.sub(r"[^\x00-\x7F]+", "", str(t)).strip()

def split_stuck_name(name):
    """Splits stuck words like 'RamjeetSingh' -> 'Ramjeet Singh'"""
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", name)

# 2. DOB EXTRACTION (Universal Logic)
def find_dob_oldest(entries):
    full_dates = []
    year_dates = []

    # NEW REGEX: Universally matches DD/MM/YYYY
    # Allows separators: / (slash), - (dash), . (dot), or whitespace
    # Captures: Group 1 (Day), Group 2 (Month), Group 3 (Year)
    universal_date_pattern = r"(\d{2})[\s\/\.-]+(\d{2})[\s\/\.-]+(\d{4})"
    
    # Regex for Year Only: Matches 19xx or 20xx
    year_pattern = r"\b(19\d{2}|20\d{2})\b"

    for e in entries:
        text = e["text"]
        
        # --- A. Search for FULL DATES (Priority) ---
        matches = re.findall(universal_date_pattern, text)
        for d_str, m_str, y_str in matches:
            try:
                d, m, y = int(d_str), int(m_str), int(y_str)
                
                # Validation: Year between 1900-2025, Month 1-12, Day 1-31
                if 1900 < y < 2025 and 1 <= m <= 12 and 1 <= d <= 31:
                    dt_obj = datetime(y, m, d)
                    # Standardize format to DD/MM/YYYY for display
                    formatted_date = f"{d:02d}/{m:02d}/{y}"
                    full_dates.append((dt_obj, formatted_date))
            except: 
                continue

        # --- B. Search for YEAR ONLY (Fallback) ---
        # Only add to list if it looks like a birth year
        y_matches = re.findall(year_pattern, text)
        for y_str in y_matches:
            y_int = int(y_str)
            if 1900 < y_int < 2025:
                year_dates.append(y_str)

    # --- FINAL DECISION LOGIC ---

    # 1. If any FULL DATE was found, ignore years. Pick the OLDEST full date.
    if full_dates:
        # Sort by datetime object (oldest first)
        full_dates.sort(key=lambda x: x[0]) 
        return full_dates[0][1] # Return the string "01/09/1981"

    # 2. If NO full date found, pick the OLDEST Year.
    if year_dates:
        # Sort numerically
        year_dates.sort(key=int)
        return year_dates[0] # Return the string "1981"

    return None

# 3. NAME EXTRACTION
def extract_name(text_list):
    candidates = []
    for t in text_list:
        t = clean_text(t)
        if len(t) < 3 or re.search(r"\d", t): continue
        if any(bad in t.upper() for bad in ["INDIA", "GOV", "DOB", "MALE", "FEMALE", "AADHAAR", "VID"]): continue
        
        words = t.split()
        if len(words) < 2: continue
        t = split_stuck_name(t)
        candidates.append(t)
    return max(candidates, key=len) if candidates else None

# 4. GENDER EXTRACTION
def extract_gender(full_text_str):
    text_lower = full_text_str.lower()
    
    # Check Female FIRST
    if re.search(r'\b(female|fem)\b', text_lower):
        return "Female"
    
    # THEN Check Male
    elif re.search(r'\b(male)\b', text_lower):
        return "Male"
        
    return None

# 5. MAIN FUNCTION
def extract_fields(ocr_json):
    raw_texts = ocr_json.get("rec_texts", [])
    entries = []
    flat_texts = []
    
    for item in raw_texts:
        txt = ""
        if isinstance(item, list):
            for sub in item:
                if isinstance(sub, tuple): txt = sub[0]
                elif isinstance(sub, str): txt = sub
                flat_texts.append(txt)
                entries.append({"text": txt})
        elif isinstance(item, str):
            txt = item
            flat_texts.append(txt)
            entries.append({"text": txt})

    full_text_str = " ".join(flat_texts)

    # Call the updated DOB logic
    dob = find_dob_oldest(entries)
    
    aadhaar = None
    m = re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", full_text_str)
    if m: aadhaar = m.group().replace(" ", "")

    gender = extract_gender(full_text_str)

    name = extract_name(flat_texts)

    return {
        "name": name, "dob": dob, "gender": gender, "aadhaar_number": aadhaar
    }