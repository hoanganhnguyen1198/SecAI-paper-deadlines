# %%
from datetime import datetime, time, timedelta

# %%
import yaml
import requests
import csv

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
all_ai_keys = set()
for conference in ai_conferences:
    all_ai_keys.update(conference.keys())

# %%
all_sec_keys = set()
for conference in sec_conferences:
    all_sec_keys.update(conference.keys())

# %%
all_mpc_keys = set()
for conference in mpc_conferences:
    all_mpc_keys.update(conference.keys())

# %%
def convertYMLToCsv(conferences, csv_path, fieldnames):
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
        writer.writeheader()

        for conference in conferences:
            row = {}
            for key in fieldnames:
                value = conference.get(key, "")
                if isinstance(value, list):
                    row[key] = " | ".join(map(str, value))
                elif isinstance(value, dict):
                    row[key] = yaml.safe_dump(value, default_flow_style=True).strip()
                else:
                    row[key] = value
            writer.writerow(row)

# %%
sec_csv_path = SEC_CONFERENCES_FILE_PATH.replace(".yml", ".csv")
ai_csv_path = AI_CONFERENCES_FILE_PATH.replace(".yml", ".csv")
mpc_csv_path = MPC_CONFERENCES_FILE_PATH.replace(".yml", ".csv")

convertYMLToCsv(sec_conferences, sec_csv_path, all_sec_keys)
convertYMLToCsv(ai_conferences, ai_csv_path, all_ai_keys)
convertYMLToCsv(mpc_conferences, mpc_csv_path, all_mpc_keys)

print(f"Saved: {sec_csv_path}")
print(f"Saved: {ai_csv_path}")
print(f"Saved: {mpc_csv_path}")

