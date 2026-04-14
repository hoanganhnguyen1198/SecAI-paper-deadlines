# %%
from datetime import datetime, time, timedelta

# %%
import yaml
import requests

# %%
SEC_CONFERENCES_URL = "https://raw.githubusercontent.com/sec-deadlines/sec-deadlines.github.io/master/_data/conferences.yml"
AI_CONFERENCES_URL = "https://raw.githubusercontent.com/paperswithcode/ai-deadlines/gh-pages/_data/conferences.yml"
MPC_CONFERENCES_URL = "https://raw.githubusercontent.com/mpc-deadlines/mpc-deadlines.github.io/master/_data/conferences.yml"

# %%
SEC_CONFERENCES_FILE_PATH = "resources/sec_conferences.yml"
AI_CONFERENCES_FILE_PATH = "resources/ai_conferences.yml"
MPC_CONFERENCES_FILE_PATH = "resources/mpc_conferences.yml"

# %%
def downloadConferencesYAML(url: str, save_path: str):
    response = requests.get(url)
    response.raise_for_status()  # Ensure request succeeded
    
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"Downloaded {save_path} successfully!")

# %%
downloadConferencesYAML(SEC_CONFERENCES_URL, SEC_CONFERENCES_FILE_PATH)
downloadConferencesYAML(AI_CONFERENCES_URL, AI_CONFERENCES_FILE_PATH)
downloadConferencesYAML(MPC_CONFERENCES_URL, MPC_CONFERENCES_FILE_PATH)

# %%
with open(SEC_CONFERENCES_FILE_PATH, "r", encoding="utf-8") as f:
    sec_conferences = yaml.safe_load(f)

with open(AI_CONFERENCES_FILE_PATH, "r", encoding="utf-8") as f:
    ai_conferences = yaml.safe_load(f)

with open(MPC_CONFERENCES_FILE_PATH, "r", encoding="utf-8") as f:
    mpc_conferences = yaml.safe_load(f)

# %%
def renameTypoKeys(conference):
    if "data" in conference:
        conference["date"] = conference.pop("data", None)
        conference["note"] = conference.pop("Note", None)

# %%
def addRankToConferenceFromTags(conference):
    tag_list = conference.get("tags", [])
    rank = "Not Ranked"
    if "TOP4" in tag_list:
        rank = "TOP4"
    elif "ASTAR" in tag_list or "COREAS" in tag_list:
        rank = "A*"
    elif "COREA" in tag_list or "CORE-A" in tag_list:
        rank = "A"
    elif "COREB" in tag_list or "CORE-B" in tag_list:
        rank = "B"
    elif "COREC" in tag_list or "CORE-C" in tag_list:
        rank = "C"
    else:
        rank = "Not Ranked"
    conference["rank"] = rank

# %%
def mergeCommentToNote(conference):
    if "comment" in conference:
        comment = conference.pop("comment", "None")
        if "note" in conference:
            conference["note"] += f" {comment}"
        else:
            conference["note"] = comment

# %%
def standardiseTimezone(conference):
    if "timezone" in conference:
        tz = conference["timezone"].strip().upper()
        if tz in ["UTC", "GMT"]:
            conference["timezone"] = "UTC"
        elif tz in ["PT", "PST", "PDT"]:
            conference["timezone"] = "America/Los_Angeles"
        elif tz in ["EST", "EDT"]:
            conference["timezone"] = "America/New_York"
        elif tz in ["CET", "CEST"]:
            conference["timezone"] = "Europe/Paris"
        else:
            conference["timezone"] = tz  # Keep as is if unrecognized

# %%
deleted_key_list = [
    "dblp",
    "comment",
    "conference",
    "portal",
    "rebut",
    "tags",
    "sub",
    "id",
    "start",
    "end",
    "paperslink",
    "pwclink",
]

# %%
def processSecConferences(sec_conferences):
    for conf in sec_conferences:
        addRankToConferenceFromTags(conf)
        mergeCommentToNote(conf)
        standardiseTimezone(conf)
        if "abdeadline" in conf:
            conf["abstract_deadline"] = conf.pop("abdeadline", None)
        for key in deleted_key_list:
            conf.pop(key, None)

# %%
def processAIConferences(ai_conferences):
    for conf in ai_conferences:
        conf["name"] = conf.pop("title", None)
        conf["description"] = conf.pop("full_name", None)
        renameTypoKeys(conf)
        for key in deleted_key_list:
            conf.pop(key, None)

# %%
processAIConferences(ai_conferences)
processSecConferences(sec_conferences)
processSecConferences(mpc_conferences)

# %%
combined_conferences = sec_conferences + ai_conferences + mpc_conferences

# %%
with open("resources/combined_conferences.yaml", "w", encoding="utf-8") as f:
    yaml.dump(combined_conferences, f, default_flow_style=False, sort_keys=False)


