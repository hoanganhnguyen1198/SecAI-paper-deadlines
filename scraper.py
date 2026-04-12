import requests
from bs4 import BeautifulSoup
import pandas as pd


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_html(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text


# -----------------------------
# AI Deadlines
# -----------------------------
def parse_ai_deadlines():
    url = "http://aideadlines.org/?sub=ML,CV,NLP,RO,SP,DM,AP,KR,HCI,IRSM,MISC"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    conferences = []

    for row in soup.select("tr"):
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        name = cols[0].get_text(strip=True)
        deadline = cols[2].get_text(strip=True)
        date = cols[3].get_text(strip=True)
        location = cols[4].get_text(strip=True)

        conferences.append({
            "EventName": name,
            "Category": "AI",
            "SubmissionDeadline": deadline,
            "Location": location,
            "EventDate": date,
            "Rank": "A*/A/B (heuristic)"
        })

    return conferences


# -----------------------------
# Security Deadlines
# -----------------------------
def parse_sec_deadlines():
    url = "https://sec-deadlines.github.io/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    conferences = []

    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        name = cols[0].get_text(strip=True)
        deadline = cols[1].get_text(strip=True)
        date = cols[2].get_text(strip=True)
        location = cols[3].get_text(strip=True)

        conferences.append({
            "EventName": name,
            "Category": "Security",
            "SubmissionDeadline": deadline,
            "Location": location,
            "EventDate": date,
            "Rank": "Top-tier / Mid-tier (manual)"
        })

    return conferences


# -----------------------------
# MPC Deadlines
# -----------------------------
def parse_mpc_deadlines():
    url = "https://mpc-deadlines.github.io/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    conferences = []

    for row in soup.select("table tr"):
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        name = cols[0].get_text(strip=True)
        deadline = cols[1].get_text(strip=True)
        date = cols[2].get_text(strip=True)
        location = cols[3].get_text(strip=True)

        conferences.append({
            "EventName": name,
            "Category": "MPC",
            "SubmissionDeadline": deadline,
            "Location": location,
            "EventDate": date,
            "Rank": "Cryptography-focused"
        })

    return conferences


# -----------------------------
# IACR Events (Cryptology)
# -----------------------------
def parse_iacr_events():
    url = "https://www.iacr.org/events/"
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    conferences = []

    for event in soup.select(".event"):
        name = event.find("h2")
        date = event.find(class_="date")
        location = event.find(class_="location")

        conferences.append({
            "EventName": name.get_text(strip=True) if name else None,
            "Category": "Cryptology",
            "SubmissionDeadline": None,  # Not always listed
            "Location": location.get_text(strip=True) if location else None,
            "EventDate": date.get_text(strip=True) if date else None,
            "Rank": "IACR flagship"
        })

    return conferences


# -----------------------------
# Main Aggregation
# -----------------------------
def main():
    all_conferences = []

    try:
        all_conferences.extend(parse_ai_deadlines())
    except Exception as e:
        print("AI parsing failed:", e)

    try:
        all_conferences.extend(parse_sec_deadlines())
    except Exception as e:
        print("Security parsing failed:", e)

    try:
        all_conferences.extend(parse_mpc_deadlines())
    except Exception as e:
        print("MPC parsing failed:", e)

    try:
        all_conferences.extend(parse_iacr_events())
    except Exception as e:
        print("IACR parsing failed:", e)

    df = pd.DataFrame(all_conferences)

    # Clean duplicates
    df.drop_duplicates(subset=["EventName"], inplace=True)

    # Save CSV
    df.to_csv("conference_deadlines.csv", index=False)

    print("Saved conference_deadlines.csv")
    print(df.head())


if __name__ == "__main__":
    main()