# %%
import pandas as pd
from pathlib import Path

# %%
SEC_CONFERENCES_FILE_PATH = "resources/sec_conferences.csv"
AI_CONFERENCES_FILE_PATH = "resources/ai_conferences.csv"
MPC_CONFERENCES_FILE_PATH = "resources/mpc_conferences.csv"

# %%
sec_df = pd.read_csv(SEC_CONFERENCES_FILE_PATH)
ai_df = pd.read_csv(AI_CONFERENCES_FILE_PATH)
mpc_df = pd.read_csv(MPC_CONFERENCES_FILE_PATH)

# %%
# Keep all columns from both dataframes, adding new ones as needed
all_columns = sec_df.columns.union(mpc_df.columns)

sec_df = pd.concat(
    [sec_df.reindex(columns=all_columns), mpc_df.reindex(columns=all_columns)],
    ignore_index=True
)

# %%
def addRankToConferencesFromTags(df):
    if "tags" not in df.columns:
        raise ValueError("The dataframe must contain a 'tags' column.")

    for idx, tags in df["tags"].items():
        if isinstance(tags, str):
            tag_list = [tag.strip() for tag in tags.split("|")]
            if "TOP4" in tag_list:
                df.at[idx, "rank"] = "TOP4"
            elif "ASTAR" in tag_list or "COREAS" in tag_list:
                df.at[idx, "rank"] = "A*"
            elif "COREA" in tag_list or "CORE-A" in tag_list:
                df.at[idx, "rank"] = "A"
            elif "COREB" in tag_list or "CORE-B" in tag_list:
                df.at[idx, "rank"] = "B"
            elif "COREC" in tag_list or "CORE-C" in tag_list:
                df.at[idx, "rank"] = "C"
            else:
                df.at[idx, "rank"] = "Not Ranked"

# %%
addRankToConferencesFromTags(sec_df)

# %%
def appendYearToConferenceName(df):
    if "name" not in df.columns or "year" not in df.columns:
        raise ValueError("The dataframe must contain 'name' and 'year' columns.")

    for idx, (name, year) in df[["name", "year"]].iterrows():
        if pd.notna(year) and pd.notna(name):
            try:
                df.at[idx, "name"] = f"{name} {year}"
            except Exception as e:
                print(f"Error parsing date for conference '{name}': {e}")

# %%
appendYearToConferenceName(sec_df)

# %%
def appendYearToConferenceDate(df):
    if "date" not in df.columns or "year" not in df.columns:
        raise ValueError("The dataframe must contain 'date' and 'year' columns.")

    for idx, (date, year) in df[["date", "year"]].iterrows():
        if pd.notna(year) and pd.notna(date):
            try:
                df.at[idx, "date"] = f"{date} {year}"
            except Exception as e:
                print(f"Error parsing date for conference with date '{date}': {e}")

# %%
appendYearToConferenceDate(sec_df)

# %%
def lambdaMergeNoteAndComment(row):
        note = str(row["note"]).strip() if pd.notna(row["note"]) else ""
        comment = str(row["comment"]).strip() if pd.notna(row["comment"]) else ""

        if note and comment:
            return f"{note}. {comment}"
        if note:
            return note
        if comment:
            return comment
        return pd.NA
def mergeNoteAndComment(df):
    if "note" not in df.columns or "comment" not in df.columns:
        raise ValueError(
            "The dataframe must contain both 'note' and 'comment' columns."
        )

    df["note"] = df.apply(lambdaMergeNoteAndComment, axis=1)


# %%
mergeNoteAndComment(sec_df)

# %%
def lambdaConcatenateYearToDeadlineIfMissing(row):
    missing_year = isinstance(row["deadline"], str) and ("%Y" in row["deadline"])
    if missing_year and pd.notna(row["year"]):
        parsed_year = pd.to_datetime(row["year"]).year
        return str(row["deadline"]).replace("%Y", str(parsed_year))
    return row["deadline"]
def concatenateYearToDeadlineIfMissing(df):
    df["deadline"] = df.apply(lambdaConcatenateYearToDeadlineIfMissing, axis=1)

# %%
concatenateYearToDeadlineIfMissing(sec_df)

# %%
def splitMultipleDeadlinesIntoSeparateRows(df):
    if "deadline" not in df.columns:
        raise ValueError("'deadline' column not found in df.")

    # Split multiple deadlines into lists, then create one row per deadline
    df = df.assign(
        deadline=df["deadline"].apply(
            lambda x: [d.strip() for d in x.split("|")] if isinstance(x, str) else [x]
        )
    ).explode("deadline", ignore_index=True)

    # Normalize empty values after split
    df["deadline"] = df["deadline"].replace("", pd.NA)

    return df

# %%
sec_df = splitMultipleDeadlinesIntoSeparateRows(sec_df)

# %%
sec_df.rename(columns={"description": "full_name"}, inplace=True)
sec_df.rename(columns={"place": "location"}, inplace=True)
sec_df.rename(columns={"abdeadline": "abstract_deadline"}, inplace=True)

# %%
sec_df.fillna({"abstract_deadline": "None", "timezone": "Unknown", "note": "None"}, inplace=True)

# %%
sec_df.drop(columns=["dblp", "tags", "year", "comment", "rebut", "portal", "conference"], inplace=True)

# %%
sec_df.to_csv("resources/final_sec_conferences.csv", index=False)


