import re


def extract_judge_and_court(text):
    header = " ".join(text.splitlines()[:60])
    judge = "Not detected"
    court = "Not detected"
    judge_patterns = (
        r"Hon['’]?ble\s+(?:Mr\.?\s+)?Justice\s+([A-Z][A-Za-z .'-]+?)(?=\s+(?:Date|Dated)\b|$)",
        r"Justice\s+([A-Z][A-Za-z .'-]+?)(?=\s+(?:Date|Dated)\b|$)",
    )
    court_patterns = (
        r"Supreme Court of India", r"High Court of [A-Za-z ]+",
        r"District Court of [A-Za-z ]+", r"Family Court of [A-Za-z ]+",
        r"Labour Court of [A-Za-z ]+",
    )
    for pattern in judge_patterns:
        match = re.search(pattern, header, re.IGNORECASE)
        if match:
            judge = match.group(1).strip()
            break
    for pattern in court_patterns:
        match = re.search(pattern, header, re.IGNORECASE)
        if match:
            court = match.group(0).strip()
            break
    return judge, court


def extract_case_date(text):
    match = re.search(r"\b(?: dated |date[:\s]+)?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text, re.IGNORECASE)
    return match.group(1) if match else "Not detected"
