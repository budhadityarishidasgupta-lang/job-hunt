import re
import pandas as pd
from bs4 import BeautifulSoup


# ---------------------------------------------------------
# Clean text (remove HTML, whitespace)
# ---------------------------------------------------------

def clean_text(text: str) -> str:
    if not text:
        return ""

    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ---------------------------------------------------------
# Create a safe snippet of text
# ---------------------------------------------------------

def make_snippet(text: str, length: int = 300) -> str:
    if not text:
        return ""
    text = clean_text(text)
    return text[:length]


# ---------------------------------------------------------
# Convert match results to CSV (as bytes)
# ---------------------------------------------------------

def results_to_csv(results: list) -> bytes:
    """
    Converts a list of job match dictionaries to downloadable CSV bytes.
    """

    if not results:
        return b""

    df = pd.DataFrame(results)
    return df.to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------
# Safe getter
# ---------------------------------------------------------

def safe_get(obj: dict, key: str, default=""):
    try:
        return obj.get(key, default)
    except:
        return default


