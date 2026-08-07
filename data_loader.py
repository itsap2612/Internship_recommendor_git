# data_loader.py
import os
import requests
from itertools import zip_longest

# ------------------------------
# API KEYS (replace with your own if needed)
# ------------------------------
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY", "api_key")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "api_key")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "api_key")

# ✅ USAJOBS details
USAJOBS_USER_AGENT = os.getenv("USAJOBS_USER_AGENT", "email@xyz")  # must be registered email
USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY", "api_key")


# ------------------------------
# Jooble Loader
# ------------------------------
def load_internships_from_jooble(query="internship", location="India", top_k=20):
    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    payload = {"keywords": query, "location": location, "page": 1, "size": top_k}

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = []
        for i, item in enumerate(data.get("jobs", [])):
            results.append({
                "id": f"jooble-{i}",
                "title": item.get("title", "N/A"),
                "company": item.get("company", "N/A"),
                "location": item.get("location", "N/A"),
                "description": item.get("snippet", "No description"),
                "link": item.get("link", "#"),
                "salary": item.get("salary", "Not disclosed"),
                "source": "jooble"
            })
        return results
    except Exception as e:
        print(f"[Jooble] Request failed: {e}")
        return []


# ------------------------------
# Adzuna Loader
# ------------------------------
def load_internships_from_adzuna(query="internship", location="India", top_k=20):
    url = f"https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": top_k,
        "what": query,
        "where": location
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = []
        for i, item in enumerate(data.get("results", [])):
            results.append({
                "id": f"adzuna-{i}",
                "title": item.get("title", "N/A"),
                "company": item.get("company", {}).get("display_name", "N/A"),
                "location": item.get("location", {}).get("display_name", "N/A"),
                "description": item.get("description", "No description"),
                "link": item.get("redirect_url", "#"),
                "salary": item.get("salary_min", "Not disclosed"),
                "source": "adzuna"
            })
        return results
    except Exception as e:
        print(f"[Adzuna] Request failed: {e}")
        return []


# ------------------------------
# USAJOBS Loader
# ------------------------------
def load_internships_from_usajobs(query="internship", location="USA", top_k=20):
    url = "https://data.usajobs.gov/api/search"
    params = {"Keyword": query, "LocationName": location}

    headers = {
        "User-Agent": USAJOBS_USER_AGENT,
        "Authorization-Key": USAJOBS_API_KEY,
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        results = []
        for i, item in enumerate(data.get("SearchResult", {}).get("SearchResultItems", [])):
            job = item.get("MatchedObjectDescriptor", {})
            results.append({
                "id": f"usajobs-{i}",
                "title": job.get("PositionTitle", "N/A"),
                "company": job.get("OrganizationName", "N/A"),
                "location": job.get("PositionLocationDisplay", "N/A"),
                "description": job.get("UserArea", {}).get("Details", {}).get("JobSummary", "No description"),
                "link": job.get("PositionURI", "#"),
                "salary": job.get("PositionRemuneration", [{}])[0].get("MinimumRange", "Not disclosed"),
                "source": "usajobs",
            })
            if len(results) >= top_k:
                break
        return results
    except Exception as e:
        print(f"[USAJOBS] Request failed: {e}")
        return []


# ------------------------------
# Combined Loader (Fair Mixing)
# ------------------------------
def load_internships_combined(query="internship", location="India", top_k=20):
    jooble = load_internships_from_jooble(query, location, top_k)
    adzuna = load_internships_from_adzuna(query, location, top_k)
    usajobs = []

    if "usa" in location.lower() or "united states" in location.lower():
        usajobs = load_internships_from_usajobs(query, "USA", top_k)

    # Round-robin mixing (Jooble + Adzuna + USAJOBS)
    mixed = []
    for triple in zip_longest(jooble, adzuna, usajobs):
        for job in triple:
            if job:
                mixed.append(job)
            if len(mixed) >= top_k:
                break
        if len(mixed) >= top_k:
            break

    # Deduplicate by (title, company, location)
    seen = set()
    unique = []
    for job in mixed:
        key = (job["title"].lower(), job["company"].lower(), job["location"].lower())
        if key not in seen:
            unique.append(job)
            seen.add(key)

    return unique[:top_k]
