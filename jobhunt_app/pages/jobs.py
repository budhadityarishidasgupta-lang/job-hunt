"""Streamlit jobs page with grouped listings and scrape stats."""

from __future__ import annotations

import hashlib
from typing import List

import streamlit as st

from data_sources import collect_jobs
from feedback import save_feedback as persist_feedback
from utils import make_snippet

DEFAULT_KEYWORDS = "HR Director OR Head of HR"
DEFAULT_COUNTRIES = ["Germany", "Netherlands", "UK"]


def _job_id(job: dict, fallback: int) -> str:
    """Create a stable identifier for a job using URL or title/company."""
    if job.get("url"):
        return hashlib.md5(job["url"].encode("utf-8")).hexdigest()
    if job.get("title") and job.get("company"):
        key = f"{job['title']}::{job['company']}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()
    return f"job-{fallback}"


def fetch_jobs(keywords: str, countries: List[str]):
    jobs = collect_jobs(keywords, countries)
    normalized = []
    for idx, job in enumerate(jobs):
        normalized.append(
            {
                "id": _job_id(job, idx),
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", "Unknown"),
                "url": job.get("url", ""),
                "source": job.get("source", "Unknown"),
                "snippet": make_snippet(job.get("description", ""), 320),
            }
        )
    return normalized


def render_feedback_state(job_id: str, value: str):
    if "feedback" not in st.session_state:
        st.session_state.feedback = {}
    st.session_state.feedback[job_id] = value


st.title("🎯 Curated HR Jobs")
st.write("Browse collected HR leadership roles and mark relevance.")

keywords = st.text_input("Search keywords", value=DEFAULT_KEYWORDS, key="keywords")
countries = st.multiselect(
    "Countries", DEFAULT_COUNTRIES, default=DEFAULT_COUNTRIES, key="countries"
)

if st.button("🔄 Refresh jobs"):
    st.session_state.jobs = fetch_jobs(keywords, countries)

# ----- Load jobs once -----
if "jobs" not in st.session_state:
    st.session_state.jobs = fetch_jobs(keywords, countries)

jobs = st.session_state.jobs

if not jobs:
    st.info("No jobs loaded yet. Fetch to see listings.")

# ----- Prepare stats -----
site_stats = {}
for job in jobs:
    site = job.get("source", "Unknown")
    site_stats[site] = site_stats.get(site, 0) + 1

# ----- Page Layout -----
left, right = st.columns([0.7, 0.3])

# RIGHT PANEL (30% width)
with right:
    st.markdown("### 📊 Scraped Jobs Summary")

    for site, count in site_stats.items():
        st.markdown(f"**{site}** — {count} postings")

    st.markdown("---")
    st.caption("Updated every scrape run")

# LEFT PANEL (70% width)
with left:
    st.markdown("## 🔍 Job Results")

    # Group jobs by job site
    jobs_by_site = {}
    for job in jobs:
        src = job.get("source", "Unknown")
        jobs_by_site.setdefault(src, []).append(job)

    # Collapsible site groups
    for site_name, site_jobs in jobs_by_site.items():
        with st.expander(f"📁 {site_name} ({len(site_jobs)} jobs)", expanded=False):
            # Group jobs by location inside each site
            jobs_by_location = {}
            for job in site_jobs:
                loc = job.get("location", "Unknown")
                jobs_by_location.setdefault(loc, []).append(job)

            for location, location_jobs in jobs_by_location.items():
                st.markdown(f"### 📍 {location} ({len(location_jobs)})")

                for job in location_jobs:
                    st.markdown(f"**{job['title']}**")
                    st.write(job.get("company"))
                    st.write(job.get("snippet", ""))

                    col1, col2 = st.columns([0.15, 0.85])

                    with col1:
                        if st.button("👍", key=f"up_{job['id']}"):
                            persist_feedback(job, 1)
                            render_feedback_state(job["id"], "up")
                            st.toast("Saved 👍")

                        if st.button("👎", key=f"down_{job['id']}"):
                            persist_feedback(job, -1)
                            render_feedback_state(job["id"], "down")
                            st.toast("Saved 👎")

                    with col2:
                        if st.button("Open Link", key=f"url_{job['id']}"):
                            st.write(f"[Open Job Posting]({job['url']})")
