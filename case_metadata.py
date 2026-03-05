'''import re

def extract_judge_and_court(text):
   court = "Not Found"

    # Only check first 50 lines to speed up
    lines = text.split("\n")[:50]
    text_head = " ".join(lines)

    # Judge detection patterns
    judge_patterns = [
        r"Hon[’']?ble\s+Mr\.?\s+Justice\s+([A-Z][a-zA-Z\s]+)",  # Hon'ble Mr. Justice X
        r"Hon[’']?ble\s+Justice\s+([A-Z][a-zA-Z\s]+)",           # Hon'ble Justice X
        r"Justice\s+([A-Z][a-zA-Z\s]+)",                          # Justice X
    ]
    for pattern in judge_patterns:
        match = re.search(pattern, text_head)
        if match:
            judge = match.group(1)
            break

    # Court detection patterns
    court_patterns = [
        r"(Supreme Court of India)",
        r"(High Court of [A-Za-z\s]+)",
        r"(District Court of [A-Za-z\s]+)",
        r"(Family Court of [A-Za-z\s]+)",
        r"(Labour Court of [A-Za-z\s]+)"
    ]
    for pattern in court_patterns:
        match = re.search(pattern, text_head)
        if match:
            court = match.group(1)
            break

    return judge, court
'''
