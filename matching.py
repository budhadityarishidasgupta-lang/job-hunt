from sentence_transformers import SentenceTransformer, util
import numpy as np


# ---------------------------------------------------------
# Load embedding model (cached for performance)
# ---------------------------------------------------------

_model = None

def load_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


# ---------------------------------------------------------
# Compute match scores between CV and job descriptions
# ---------------------------------------------------------

def compute_matches(cv_text, jobs, threshold=0.55):
    """
    cv_text : extracted text from CV
    jobs    : list of normalized job dictionaries

    Returns a list of:
    {
        title, company, source, score (0–100%), snippet, url, location
    }
    """

    model = load_model()
    cv_emb = model.encode(cv_text, convert_to_tensor=True)

    results = []

    for job in jobs:

        # Choose best text to compare
        job_text = (
            job.get("description")
            or job.get("title")
            or ""
        )

        if not job_text.strip():
            continue

        job_emb = model.encode(job_text, convert_to_tensor=True)

        # Cosine similarity
        sim = util.cos_sim(cv_emb, job_emb).item()

        if sim < threshold:
            continue

        score_pct = round(sim * 100, 2)

        snippet = job_text.strip().replace("\n", " ")[:300]

        results.append({
            "title": job.get("title", "Unknown"),
            "company": job.get("company", "N/A"),
            "source": job.get("source", "Unknown"),
            "location": job.get("location", ""),
            "url": job.get("url", ""),
            "score": score_pct,
            "snippet": snippet,
        })

    return results
