import os
import json
from openai import OpenAI
from typing import List, Dict


_client = None


def _get_client() -> OpenAI:
    """Return a cached OpenAI client instance."""
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Please add it in Streamlit secrets."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def llm_fit_score(
    cv_text: str,
    job_text: str,
    liked_examples: List[str] = None,
    disliked_examples: List[str] = None,
) -> Dict:
    """
    GPT-based preference-aware fit score.
    Returns a dict with: score, summary, strengths, gaps
    """

    liked_examples = liked_examples or []
    disliked_examples = disliked_examples or []

    preference_block = ""

    if liked_examples:
        preference_block += "Jobs the user LIKED:\n" + "\n".join(
            f"- {t}" for t in liked_examples
        ) + "\n\n"
    if disliked_examples:
        preference_block += "Jobs the user DISLIKED:\n" + "\n".join(
            f"- {t}" for t in disliked_examples
        ) + "\n\n"

    if not preference_block:
        preference_block = (
            "The user prefers senior HR, People Ops, HR Operations, "
            "and HR Transformation roles.\n\n"
        )

    prompt = f"""
Evaluate the fit between this CV and job description.

CV:
\"\"\"{cv_text[:5000]}\"\"\"

Job Description:
\"\"\"{job_text[:5000]}\"\"\"

User preference history:
{preference_block}

Return ONLY valid JSON with fields:
- "score": number 0-100
- "summary": short string
- "strengths": list of strings
- "gaps": list of strings
    """

    client = _get_client()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    try:
        raw = response.output[0].content[0].text
        data = json.loads(raw)
    except Exception:
        data = {
            "score": None,
            "summary": raw[:400] if isinstance(raw, str) else "",
            "strengths": [],
            "gaps": [],
        }

    return data

