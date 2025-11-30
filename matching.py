from sentence_transformers import SentenceTransformer, util


# ---------------------------------------------------------
# Load MPNet embedding model (high-accuracy)
# ---------------------------------------------------------

_model = None

def load_model():
    global _model
    if _model is None:
        # Higher quality model for CV <-> JD matching
        _model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _model


# ---------------------------------------------------------
# Compute match scores between CV and job descriptions
# ---------------------------------------------------------

def compute_matches(cv_text, jobs, threshold=0.30):
    """
    CV vs Job Description semantic similarity.
    Uses all-mpnet-base-v2 for deeper matching accuracy.
    """

    model = load_model()
    cv_emb = model.encode(cv_text, convert_to_tensor=True)

    results = []

    for job in jobs:

        # Use ONLY job description (title is not used for matching)
        job_desc = job.get("description", "").strip()

        if not job_desc:
            continue

        job_emb = model.encode(job_desc, convert_to_tensor=True)
        sim = util.cos_sim(cv_emb, job_emb).item()

        if sim < threshold:
            continue

        score_pct = round(sim * 100, 2)

        snippet = job_desc.replace("\n", " ")[:300]

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
