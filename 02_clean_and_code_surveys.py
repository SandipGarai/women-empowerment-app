# %%
# Step 1: Import libraries and define file paths
# This script cleans and codes the survey data after initial exploration.
# It is written in VS Code / ipykernel style, so each # %% block can be run as a cell.

from pathlib import Path
import re
import sys
import unicodedata

import pandas as pd


# Windows terminals sometimes use a legacy encoding.
# UTF-8 allows Hindi/local-language responses to print correctly.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    # display gives nicer tables inside VS Code notebooks / ipykernel.
    from IPython.display import display
except ImportError:
    # Plain Python fallback so this script can also run from the terminal.
    display = print


# Path to the current project folder.
PROJECT_DIR = Path(__file__).resolve().parent

# Input workbook.
EXCEL_PATH = PROJECT_DIR / "Surveys.xlsx"

# Output folder for cleaned and coded data.
OUTPUT_DIR = PROJECT_DIR / "outputs" / "cleaned"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# %%
# Step 2: Load all survey sheets and reshape them to long format
# Original workbook layout:
# - One sheet per respondent group.
# - One row per question.
# - One column per respondent.

metadata_columns = ["Question No", "Section", "Particular", "Question"]

excel_file = pd.ExcelFile(EXCEL_PATH)
survey_sheets = {
    sheet_name: pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    for sheet_name in excel_file.sheet_names
}

long_tables = []

for sheet_name, df in survey_sheets.items():
    # Standardize metadata column names by using the known question descriptor columns.
    respondent_columns = [col for col in df.columns if col not in metadata_columns]

    # Convert each respondent column into rows.
    long_df = df.melt(
        id_vars=metadata_columns,
        value_vars=respondent_columns,
        var_name="respondent_id",
        value_name="response_raw",
    )

    # Add respondent group from sheet name.
    long_df.insert(0, "respondent_group", sheet_name)
    long_tables.append(long_df)

survey_long = pd.concat(long_tables, ignore_index=True)

# Keep only nonblank responses for coding.
survey_clean = survey_long.dropna(subset=["response_raw"]).copy()

# Store a text version while preserving response_raw for audit.
survey_clean["response_text"] = survey_clean["response_raw"].astype(str).str.strip()

print(f"Rows with nonblank responses: {len(survey_clean):,}")
display(survey_clean.head(10))


# %%
# Step 3: Define helper functions for text cleaning
# These helpers make the coding rules readable and reusable.

def normalize_text(value):
    """Return a lightly normalized text value for matching."""
    text = str(value).strip()

    # Normalize Unicode compatibility forms.
    text = unicodedata.normalize("NFKC", text)

    # Replace common dash variants with a simple hyphen.
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", text)

    # Replace curly apostrophes with straight apostrophes.
    text = text.replace("\u2018", "'").replace("\u2019", "'")

    # Remove checkbox marks and repeated whitespace.
    text = text.replace("\u2714", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def compact_key(value):
    """Return a lowercase matching key with light punctuation normalization."""
    text = normalize_text(value).lower()

    # Convert punctuation separators to spaces for easier matching.
    text = re.sub(r"[,+;/()]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_any(text, words):
    """Check whether any keyword occurs in a text value."""
    return any(word in text for word in words)


# %%
# Step 4: Mark profile or identifier questions
# These variables are useful for context, but we usually exclude names/locations
# from analytical frequency tables. We use exact or short-phrase matching so that
# substantive questions about Panchayat/Gram Sabha meetings are not excluded.

profile_keywords = [
    "name",
    "who the mukhiya",
]

# Location identifiers are usually single-word questions (Village, Panchayat, etc.)
# or phrases that identify the respondent. We match them as whole words/phrases
# rather than substrings.
profile_whole_phrases = [
    "village",
    "panchayat",
    "block",
    "district",
]


def is_profile_or_identifier_question(question_text):
    """Return True if the question is a profile/identifier field."""
    text = str(question_text).lower().strip()
    # Keyword substrings (e.g., "Name (Optional)")
    if contains_any(text, profile_keywords):
        return True
    # Whole-word/short phrase identifiers: question text is essentially just
    # the location word, optionally with "(Optional)" or punctuation.
    cleaned = re.sub(r"[^a-z0-9\s]", "", text).strip()
    for phrase in profile_whole_phrases:
        if cleaned == phrase or cleaned.startswith(phrase + " "):
            return True
    return False


survey_clean["question_key"] = survey_clean["Question"].astype(str).str.lower()
survey_clean["is_profile_or_identifier"] = survey_clean["Question"].apply(
    is_profile_or_identifier_question
)

display(
    survey_clean[["respondent_group", "Question No", "Question", "is_profile_or_identifier"]]
    .drop_duplicates()
    .head(20)
)


# %%
# Step 5: Define conservative coding rules
# The goal is not to force every open-ended answer into a category.
# We code obvious variants and leave uncertain answers visible for review.

def code_response(question, response):
    """Return cleaned response, broad code, and a short cleaning note."""
    question_key = compact_key(question)
    raw_text = str(response).strip()
    text = normalize_text(raw_text)
    key = compact_key(text)

    # Default: only normalized punctuation/spacing has changed.
    response_clean = text
    response_code = text
    cleaning_note = "normalized_text_only"

    # Non-answer entries that were typed as text. Each is kept as a distinct
    # response category because the user wants every nonblank cell treated as a
    # response. Blank cells are filtered out earlier.
    non_answer_map = {
        "": None,  # blank is handled before this function is called
        "na": "NA",
        "n a": "NA",
        "n/a": "NA",
        "not available": "Not available",
        "not mentioned": "Not mentioned",
        "none": "None",
        "no response": "No response",
        "dont know": "Do not know",
        "don't know": "Do not know",
        "i don't know": "Do not know",
        "i dont know": "Do not know",
        "unsure": "Unsure",
    }
    if key in non_answer_map:
        val = non_answer_map[key]
        if val is not None:
            return val, "non_answer", "coded_non_answer"

    # Gender and sex labels.
    if "gender" in question_key or question_key in {"sex"}:
        if key in {"m", "male", "man"}:
            return "Male", "male", "coded_gender"
        if key in {"f", "female", "woman", "women", "w"}:
            return "Female/Woman", "female_woman", "coded_gender"

    # Age-group labels.
    if "age group" in question_key:
        if key in {"18-25", "18 25"}:
            return "18-25", "18_25", "coded_age_group"
        if key in {"26-40", "26 40"}:
            return "26-40", "26_40", "coded_age_group"
        if key in {"41-60", "41 60"}:
            return "41-60", "41_60", "coded_age_group"
        if "more than 60" in key or "above 60" in key or key in {"60+", "more 60"}:
            return "More than 60", "more_than_60", "coded_age_group"

    # Community labels.
    if "community" in question_key:
        if "oraon" in key or key == "st":
            return "ST/Oraon", "st_oraon", "coded_community"
        if "kujur" in key:
            return "ST/Kujur", "st_kujur", "coded_community"
        if "obc" in key:
            return "OBC", "obc", "coded_community"
        if "christian" in key:
            return "Christian", "christian", "coded_community"
        if "general" in key:
            return "General", "general", "coded_community"

    # Yes/no style questions.
    yes_no_question_terms = [
        "would you go",
        "improved",
        "helpful",
        "support woman",
        "reservation",
        "successful",
    ]
    if contains_any(question_key, yes_no_question_terms):
        if key in {"yes", "yes very helpful", "very", "very helpful", "yes situation has been improved"}:
            return "Yes", "yes", "coded_yes_no"
        if key.startswith("yes "):
            return text, "yes_qualified", "coded_yes_qualified"
        if key in {"no", "not helped", "no nothing has improved", "situation has worsened more"}:
            return "No", "no", "coded_yes_no"
        if "don't know" in key or "dont know" in key or "no openion" in key or "no opinion" in key:
            return "Do not know", "do_not_know", "coded_unsure"

    # Help received from Mukhiya.
    if "did they help" in question_key:
        if "never" in key and ("went" in key or "visited" in key):
            return "Never visited", "never_visited", "coded_help_status"
        if "didn't listen" in key or "didnt listen" in key:
            return "Did not listen", "did_not_listen", "coded_help_status"
        if "not helped" in key or "not help" in key or key == "no":
            if "listen" in key:
                return "Listened but did not help", "listened_not_helped", "coded_help_status"
            return "Not helped", "not_helped", "coded_help_status"
        if "helped a little" in key:
            return "Helped a little", "partly_helped", "coded_help_status"
        if "helped" in key or key == "yes":
            return "Listened and helped", "listened_and_helped", "coded_help_status"

    # Mobile phone ownership/type.
    if "mobile phone" in question_key:
        if "smart" in key:
            return "Smart phone", "smart_phone", "coded_phone_type"
        if "basic" in key or "simple" in key:
            return "Basic/simple phone", "basic_phone", "coded_phone_type"
        if key == "no":
            return "No phone", "no_phone", "coded_phone_type"

    # Contact route to Mukhiya.
    if "contact mukhiya" in question_key:
        has_visit = contains_any(key, ["visit", "house", "go to"])
        has_call = contains_any(key, ["call", "mobile"])
        has_intermediary = contains_any(key, ["someone", "through"])
        if has_visit and has_call:
            return "Visit and phone call", "visit_and_call", "coded_contact_route"
        if has_visit and has_intermediary:
            return "Visit through someone", "visit_through_someone", "coded_contact_route"
        if has_visit:
            return "Direct visit", "direct_visit", "coded_contact_route"
        if has_call:
            return "Phone call", "phone_call", "coded_contact_route"

    # Where people go for disputes.
    if "where do people go for disputes" in question_key:
        if "both" in key:
            return "Both Mukhiya and traditional leader", "both_formal_traditional", "coded_dispute_forum"
        if "mukhiya" in key or "gram panchayat" in key:
            return "Mukhiya/Gram Panchayat", "formal_panchayat", "coded_dispute_forum"
        if "traditional" in key or "pradhan" in key:
            return "Traditional Pradhan", "traditional_pradhan", "coded_dispute_forum"

    # Attitude about women as leaders.
    if "can a woman be a good mukhiya" in question_key:
        if key == "yes" or contains_any(key, ["very good", "as good", "equal", "she can"]):
            return "Women can be good/equal leaders", "women_can_lead", "coded_attitude"
        if "man" in key and "better" in key:
            return "Prefer male leader", "prefer_male_leader", "coded_attitude"
        if "don't know" in key or "dont know" in key:
            return "Do not know", "do_not_know", "coded_attitude"

    # Land area standardization is light for now.
    if "area of land" in question_key:
        acre_match = re.search(r"(\d+(?:\.\d+)?)\s*acre", key)
        decimal_match = re.search(r"(\d+(?:\.\d+)?)\s*decimal", key)
        if acre_match:
            acres = acre_match.group(1)
            return f"{acres} acre", "land_area_reported", "coded_land_area"
        if decimal_match:
            decimals = decimal_match.group(1)
            return f"{decimals} decimal", "land_area_reported", "coded_land_area"

    # Multi-source information channels.
    if "info on schemes" in question_key:
        channels = []
        if "mukhiya" in key or "ward" in key:
            channels.append("Mukhiya/Ward member")
        if "friend" in key or "neighbour" in key or "neighbor" in key:
            channels.append("Friends/neighbours")
        if "asha" in key or "angan" in key:
            channels.append("ASHA/Anganwadi")
        if "whatsapp" in key or "social media" in key or "digital" in key:
            channels.append("Digital/social media")
        if "government" in key or "govt" in key:
            channels.append("Government officials")
        if channels:
            return " + ".join(dict.fromkeys(channels)), "multiple_info_channels", "coded_info_channels"

    # Agriculture-related multi-item answers remain mostly open-ended for now.
    agriculture_terms = ["kharif crops", "rabi crops", "livestock", "best technique"]
    if contains_any(question_key, agriculture_terms):
        return text.title(), "agriculture_open_text", "standardized_case_only"

    return response_clean, response_code, cleaning_note


# %%
# Step 6: Apply cleaning and coding rules
# The new columns make the transformation auditable.

coded_rows = survey_clean.apply(
    lambda row: code_response(row["Question"], row["response_text"]),
    axis=1,
    result_type="expand",
)

survey_clean[["response_clean", "response_code", "cleaning_note"]] = coded_rows

# Mark rows where the cleaned response changed from the text-normalized raw response.
survey_clean["response_text_normalized"] = survey_clean["response_text"].apply(normalize_text)
survey_clean["changed_by_cleaning"] = (
    survey_clean["response_clean"] != survey_clean["response_text_normalized"]
)

display(
    survey_clean[
        [
            "respondent_group",
            "Question No",
            "Question",
            "response_text",
            "response_clean",
            "response_code",
            "cleaning_note",
        ]
    ].head(25)
)


# %%
# Step 7: Build cleaned frequency tables
# Counts and percentages are calculated within each respondent group and question.

analysis_rows = survey_clean[~survey_clean["is_profile_or_identifier"]].copy()

question_totals = (
    analysis_rows.groupby(["respondent_group", "Question No"])
    .size()
    .reset_index(name="question_nonblank_n")
)

frequency_cleaned = (
    analysis_rows.groupby(
        [
            "respondent_group",
            "Question No",
            "Section",
            "Particular",
            "Question",
            "response_clean",
            "response_code",
        ],
        dropna=False,
    )
    .size()
    .reset_index(name="count")
    .merge(question_totals, on=["respondent_group", "Question No"], how="left")
)

frequency_cleaned["percent"] = (
    frequency_cleaned["count"] / frequency_cleaned["question_nonblank_n"] * 100
).round(2)

frequency_cleaned = frequency_cleaned.sort_values(
    ["respondent_group", "Question No", "count"],
    ascending=[True, True, False],
)

display(frequency_cleaned.head(40))


# %%
# Step 8: Create a review table for still-fragmented answers
# High unique-response questions may need manual thematic coding in the next step.

review_unique_responses = (
    analysis_rows.groupby(
        [
            "respondent_group",
            "Question No",
            "Section",
            "Particular",
            "Question",
            "response_clean",
            "response_code",
            "cleaning_note",
        ],
        dropna=False,
    )
    .size()
    .reset_index(name="count")
    .sort_values(["respondent_group", "Question No", "count"], ascending=[True, True, False])
)

question_cleaning_impact = (
    analysis_rows.groupby(["respondent_group", "Question No", "Question"], dropna=False)
    .agg(
        nonblank_responses=("response_clean", "size"),
        raw_unique_responses=("response_text_normalized", "nunique"),
        cleaned_unique_responses=("response_clean", "nunique"),
        coded_unique_responses=("response_code", "nunique"),
        changed_rows=("changed_by_cleaning", "sum"),
    )
    .reset_index()
)

question_cleaning_impact["unique_reduction"] = (
    question_cleaning_impact["raw_unique_responses"]
    - question_cleaning_impact["cleaned_unique_responses"]
)

question_cleaning_impact = question_cleaning_impact.sort_values(
    ["unique_reduction", "raw_unique_responses"], ascending=[False, False]
)

display(question_cleaning_impact.head(25))


# %%
# Step 9: Summarize cleaning activity
# This is a compact audit of how much the script changed.

cleaning_summary = (
    survey_clean.groupby("cleaning_note")
    .size()
    .reset_index(name="rows")
    .sort_values("rows", ascending=False)
)

cleaning_summary["percent_of_nonblank"] = (
    cleaning_summary["rows"] / len(survey_clean) * 100
).round(2)

display(cleaning_summary)


# %%
# Step 10: Save cleaned outputs
# These CSV files become the input for descriptive tables and charts.

survey_clean.to_csv(OUTPUT_DIR / "cleaned_long_responses.csv", index=False)
analysis_rows.to_csv(OUTPUT_DIR / "cleaned_analysis_responses.csv", index=False)
frequency_cleaned.to_csv(OUTPUT_DIR / "question_frequency_cleaned.csv", index=False)
review_unique_responses.to_csv(OUTPUT_DIR / "coding_review_unique_responses.csv", index=False)
question_cleaning_impact.to_csv(OUTPUT_DIR / "question_cleaning_impact.csv", index=False)
cleaning_summary.to_csv(OUTPUT_DIR / "cleaning_summary.csv", index=False)

print("Saved cleaned outputs to:")
print(OUTPUT_DIR)
