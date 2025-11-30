import requests
import feedparser
from bs4 import BeautifulSoup
import time


# ---------------------------------------------------------
# Normalize job objects into one structured format
# ---------------------------------------------------------

def normalize_job(source, title, company, location, url, description):
    return {
        "source": source or "",
        "title": title or "",
        "company": company or "",
        "location": location or "",
        "url": url or "",
        "description": description or "",
    }


# ---------------------------------------------------------
# 1. Arbeitnow API
# ---------------------------------------------------------

def fetch_arbeitnow_jobs(keywords, location):
    """
    https://www.arbeitnow.com/api/job-board-api
    """
    try:
        url = f"https://www.arbeitnow.com/api/job-board-api?keywords={keywords}&location={location}"
        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            return []

        jobs = []
        for job in resp.json().get("data", []):
            jobs.append(
                normalize_job(
                    "arbeitnow",
                    job.get("title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("url"),
                    job.get("description"),
                )
            )
        return jobs

    except Exception as e:
        print("Arbeitnow error:", e)
        return []


# ---------------------------------------------------------
# 2. Generic RSS fetcher
# ---------------------------------------------------------

def fetch_rss_jobs(url, source_name):
    try:
        feed = feedparser.parse(url)
        jobs = []
        for entry in feed.entries[:40]:
            desc = getattr(entry, "summary", getattr(entry, "description", ""))

            jobs.append(
                normalize_job(
                    source_name,
                    getattr(entry, "title", ""),
                    getattr(entry, "author", "Unknown"),
                    "",
                    getattr(entry, "link", ""),
                    desc,
                )
            )
        return jobs
    except Exception as e:
        print(f"RSS error ({source_name}):", e)
        return []


# ---------------------------------------------------------
# 3. englishjobs.de scraper (ethical)
# ---------------------------------------------------------

def scrape_englishjobs(keyword="HR"):
    try:
        url = f"https://englishjobs.de/jobs/{keyword.lower()}"
        headers = {"User-Agent": "Mozilla/5.0"}

        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs = []
        for item in soup.find_all("div", class_="job-item")[:10]:
            title = item.find("h3").text.strip() if item.find("h3") else "HR Job"
            link = item.find("a")["href"] if item.find("a") else ""

            jobs.append(
                normalize_job(
                    "englishjobs.de",
                    title,
                    "N/A",
                    "Germany",
                    link,
                    "HR / leadership role",
                )
            )

        time.sleep(5)  # ethical delay
        return jobs

    except Exception as e:
        print("englishjobs.de error:", e)
        return []


# ---------------------------------------------------------
# 4. MASTER FUNCTION — collects all jobs
# ---------------------------------------------------------

def collect_jobs(keywords, countries):
    """
    Main unified job source loader
    Returns a combined list of job dicts
    """

    all_jobs = []

    kw = keywords.replace(" ", "+")

    # Arbeitnow (only works for certain countries)
    for c in countries:
        if c in ["Germany", "Netherlands", "Spain", "Portugal"]:
            all_jobs.extend(fetch_arbeitnow_jobs(kw, c))

    # Reed (UK)
    if "UK" in countries or "United Kingdom" in countries:
        reed_url = "https://www.reed.co.uk/rss/jobs?keywords=HR+Leadership&location=London"
        all_jobs.extend(fetch_rss_jobs(reed_url, "reed"))

    # Indeed (global RSS)
    for c in countries:
        indeed_url = f"https://www.indeed.com/rss?q={kw}&l={c}"
        all_jobs.extend(fetch_rss_jobs(indeed_url, "indeed"))

    # EURES (EU)
    for c in countries:
        cc = c[:2].upper()
        eures_url = f"https://ec.europa.eu/eures/public/rss?keywords=HR&country={cc}"
        all_jobs.extend(fetch_rss_jobs(eures_url, "eures"))

    # englishjobs.de
    if "Germany" in countries:
        all_jobs.extend(scrape_englishjobs("HR"))

    print(f"[DEBUG] Arbeitnow jobs: {len([j for j in all_jobs if j['source']=='arbeitnow'])}")
    print(f"[DEBUG] Reed jobs: {len([j for j in all_jobs if j['source']=='reed'])}")
    print(f"[DEBUG] Indeed jobs: {len([j for j in all_jobs if j['source']=='indeed'])}")
    print(f"[DEBUG] EURES jobs: {len([j for j in all_jobs if j['source']=='eures'])}")
    print(f"[DEBUG] EnglishJobs jobs: {len([j for j in all_jobs if j['source']=='englishjobs.de'])}")

    # HR relevance filtering (title + description)
    HR_KEYWORDS = [
        "hr", "human resources", "people", "talent", 
        "shared services", "people operations", "people ops",
        "hr director", "head of hr", "hrbp", "people director",
        "cpo", "chief people officer"
    ]

    filtered_jobs = []
    for job in all_jobs:
        text = f"{job.get('title','')} {job.get('description','')}".lower()
        if any(kw in text for kw in HR_KEYWORDS):
            filtered_jobs.append(job)

    all_jobs = filtered_jobs

    return all_jobs
