# %%
# Step 1: Import libraries and define paths
# This script creates thesis-ready descriptive result tables from:
# - cleaned single-response frequencies
# - multi-response summaries
#
# Run cell by cell in VS Code / ipykernel, or run the whole script.

from pathlib import Path
import re
import sys

import pandas as pd


# Keep terminal output readable on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from IPython.display import display
except ImportError:
    display = print


PROJECT_DIR = Path(__file__).resolve().parent
CLEANED_DIR = PROJECT_DIR / "outputs" / "cleaned"
MULTI_RESPONSE_DIR = PROJECT_DIR / "outputs" / "multi_response"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "descriptive_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FREQUENCY_PATH = CLEANED_DIR / "question_frequency_cleaned.csv"
CLEANED_ANALYSIS_PATH = CLEANED_DIR / "cleaned_analysis_responses.csv"
MULTI_RESPONSE_SUMMARY_PATH = MULTI_RESPONSE_DIR / "multi_response_summary.csv"


# %%
# Step 2: Load cleaned and multi-response result files
# The first two phases created cleaned frequency tables.
# The third phase created corrected summaries for multi-response questions.

frequency = pd.read_csv(FREQUENCY_PATH)
analysis_rows = pd.read_csv(CLEANED_ANALYSIS_PATH)
multi_response = pd.read_csv(MULTI_RESPONSE_SUMMARY_PATH)

print(f"Single-response frequency rows: {len(frequency):,}")
print(f"Cleaned analysis response rows: {len(analysis_rows):,}")
print(f"Multi-response summary rows: {len(multi_response):,}")

display(frequency.head())
display(multi_response.head())


# %%
# Step 3: Helper functions for theme and table labels
# These functions keep the table-building logic consistent.

def clean_key(value):
    """Lowercase key for matching question text."""
    text = "" if pd.isna(value) else str(value)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return text


def normalize_question_no(value):
    """Convert question number to a stable display value."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def make_table_id(prefix, group, question_no):
    """Create a stable table id using group and question number."""
    group_key = re.sub(r"[^a-z0-9]+", "_", str(group).lower()).strip("_")
    question_key = re.sub(r"[^a-z0-9]+", "_", normalize_question_no(question_no).lower()).strip("_")
    return f"{prefix}_{group_key}_q{question_key}"


def make_detailed_table_id(prefix, group, question_no, question):
    """Create a stable table id using group, question number, and question text."""
    base_id = make_table_id(prefix, group, question_no)
    question_slug = re.sub(r"[^a-z0-9]+", "_", clean_key(question)).strip("_")[:36]
    return f"{base_id}_{question_slug}" if question_slug else base_id


def assign_theme(row):
    """Assign a thesis-oriented theme to one result row."""
    group = clean_key(row.get("respondent_group", ""))
    section = clean_key(row.get("Section", row.get("section", "")))
    particular = clean_key(row.get("Particular", row.get("particular", "")))
    question = clean_key(row.get("Question", row.get("question", "")))
    combined = " ".join([group, section, particular, question])

    # --- ICT and Digital Access (specific, check first) ---
    ict_terms = [
        "mobile", "phone", "digital", "technology", "whatsapp",
        "computer", "smartphone", "internet", "e-governance", "online",
        "social media", "sms",
    ]
    if any(term in combined for term in ict_terms):
        return "ICT and Digital Access"
    # Check "ict" and "data" as whole words to avoid matching "restrictions", "mandate", etc.
    if re.search(r"\bict\b", combined) or re.search(r"\bdata\b", combined):
        return "ICT and Digital Access"

    # --- Agriculture and Livelihood (including landholding) ---
    agriculture_terms = [
        "agriculture", "crop", "livestock", "irrigation", "landholding",
        "landholding", "land", "technique", "tractor", "drip", "farming",
        "kharif", "rabi", "paddy", "wheat", "vegetable",
    ]
    if any(term in combined for term in agriculture_terms):
        return "Agriculture and Livelihood"

    # --- Traditional vs Formal Governance ---
    traditional_terms = [
        "traditional", "formal", "pradhan", "parha", "dispute", "council",
        "mahto", "pahan", "interaction with",
    ]
    if any(term in combined for term in traditional_terms):
        return "Traditional vs Formal Governance"

    # --- Challenges and Constraints ---
    challenge_terms = [
        "challenge", "difficulty", "hurdle", "barrier", "patriarchy",
        "obstacle", "problem", "opposition",
    ]
    if any(term in combined for term in challenge_terms):
        return "Challenges and Constraints"

    # --- Women Empowerment and Panchayat Participation ---
    empowerment_terms = [
        "political journey", "participation", "decision", "gram sabha",
        "opinion", "planning", "empowerment", "mobility", "reservation",
        "proxy rule", "confidence", "respect", "leadership experience",
        "contest", "elected", "representation",
    ]
    if any(term in combined for term in empowerment_terms):
        return "Women Empowerment and Panchayat Participation"

    # --- Respondent Profile (basic demographics only) ---
    profile_terms = [
        "gender", "age", "community", "education", "marital",
        "position held", "occupation", "caste", "tribe", "name",
        "village", "panchayat", "block", "district", "income",
    ]
    if any(term in combined for term in profile_terms):
        return "Respondent Profile"

    # --- General Public awareness/access ---
    if "general public" in group and any(term in combined for term in ["awareness", "access", "mukhiya", "help", "scheme"]):
        return "General Public: Awareness and Access"

    # --- Respondent-group defaults ---
    if "govt officials" in group:
        return "Government Officials Perspective"

    if "mahila mukhiya" in group:
        return "Mahila Mukhiya Perspective"

    if "traditional leader" in group:
        return "Traditional Leader Perspective"

    if "women representative" in group:
        return "Women Empowerment and Panchayat Participation"

    return "Other"


# %%
# Step 4: Prepare single-response result tables
# Multi-response questions are excluded from this single-response set so that
# combined answers do not distort final results.

multi_response_question_keys = (
    multi_response[["respondent_group", "question_no"]]
    .drop_duplicates()
    .assign(question_no=lambda df: df["question_no"].map(normalize_question_no))
)

frequency_prepared = frequency.copy()
frequency_prepared["question_no"] = frequency_prepared["Question No"].map(normalize_question_no)

frequency_prepared = frequency_prepared.merge(
    multi_response_question_keys.assign(is_multi_response_question=True),
    on=["respondent_group", "question_no"],
    how="left",
)

single_response_results = frequency_prepared[
    frequency_prepared["is_multi_response_question"].isna()
].copy()

single_response_results["result_type"] = "single_response"
single_response_results["theme"] = single_response_results.apply(assign_theme, axis=1)
single_response_results["table_id"] = single_response_results.apply(
    lambda row: make_detailed_table_id(
        "sr", row["respondent_group"], row["question_no"], row["Question"]
    ),
    axis=1,
)

single_response_results = single_response_results[
    [
        "table_id",
        "theme",
        "result_type",
        "respondent_group",
        "question_no",
        "Section",
        "Particular",
        "Question",
        "response_clean",
        "response_code",
        "count",
        "question_nonblank_n",
        "percent",
    ]
].rename(
    columns={
        "Section": "section",
        "Particular": "particular",
        "Question": "question",
        "response_clean": "answer",
        "response_code": "answer_code",
        "question_nonblank_n": "denominator_n",
        "percent": "percent_of_respondents",
    }
)

print(f"Single-response result rows after excluding multi-response questions: {len(single_response_results):,}")
display(single_response_results.head(20))


# %%
# Step 5: Prepare multi-response result tables
# Multi-response percentages can exceed 100% within a question.

multi_response_results = multi_response.copy()

multi_response_results["question_no"] = multi_response_results["question_no"].map(normalize_question_no)
multi_response_results["result_type"] = "multi_response"
multi_response_results["theme"] = multi_response_results.apply(assign_theme, axis=1)
multi_response_results["table_id"] = multi_response_results.apply(
    lambda row: make_detailed_table_id(
        "mr", row["respondent_group"], row["question_no"], row["question"]
    ),
    axis=1,
)

multi_response_results = multi_response_results[
    [
        "table_id",
        "theme",
        "result_type",
        "respondent_group",
        "question_no",
        "question",
        "indicator_label",
        "indicator",
        "count",
        "respondents_with_answer",
        "percent_of_respondents",
    ]
].rename(
    columns={
        "indicator_label": "answer",
        "indicator": "answer_code",
        "respondents_with_answer": "denominator_n",
    }
)

multi_response_results["section"] = ""
multi_response_results["particular"] = ""

multi_response_results = multi_response_results[
    [
        "table_id",
        "theme",
        "result_type",
        "respondent_group",
        "question_no",
        "section",
        "particular",
        "question",
        "answer",
        "answer_code",
        "count",
        "denominator_n",
        "percent_of_respondents",
    ]
]

display(multi_response_results.head(20))


# %%
# Step 6: Combine all descriptive result rows
# This is the master long table for final descriptive reporting.

all_descriptive_results = pd.concat(
    [single_response_results, multi_response_results],
    ignore_index=True,
)

all_descriptive_results = all_descriptive_results.sort_values(
    ["theme", "respondent_group", "question_no", "result_type", "count"],
    ascending=[True, True, True, True, False],
)

display(all_descriptive_results.head(30))


# %%
# Step 7: Create a question-level summary table
# This gives the leading response/category for each question and helps draft findings.

question_summary_rows = []

for (table_id, theme, result_type, group, question_no, question), group_df in all_descriptive_results.groupby(
    ["table_id", "theme", "result_type", "respondent_group", "question_no", "question"],
    dropna=False,
):
    sorted_group = group_df.sort_values("count", ascending=False)
    top_row = sorted_group.iloc[0]

    question_summary_rows.append(
        {
            "table_id": table_id,
            "theme": theme,
            "result_type": result_type,
            "respondent_group": group,
            "question_no": question_no,
            "question": question,
            "denominator_n": int(top_row["denominator_n"]),
            "number_of_answer_categories": len(group_df),
            "top_answer": top_row["answer"],
            "top_count": int(top_row["count"]),
            "top_percent": float(top_row["percent_of_respondents"]),
            "note": "Percentages may exceed 100 within this question." if result_type == "multi_response" else "",
        }
    )

question_level_summary = pd.DataFrame(question_summary_rows).sort_values(
    ["theme", "respondent_group", "question_no"]
)

display(question_level_summary.head(40))


# %%
# Step 8: Create a table index
# This is a compact guide to what each final table contains.

table_index = (
    all_descriptive_results.groupby(
        ["table_id", "theme", "result_type", "respondent_group", "question_no", "question"],
        dropna=False,
    )
    .agg(
        denominator_n=("denominator_n", "max"),
        answer_rows=("answer", "count"),
        total_count=("count", "sum"),
    )
    .reset_index()
)

table_index["interpretation_note"] = table_index["result_type"].map(
    {
        "single_response": "Use count and percent as ordinary response distribution.",
        "multi_response": "Use count and percent as category mentions; percentages may exceed 100.",
    }
)

table_index = table_index.sort_values(["theme", "respondent_group", "question_no"])
display(table_index.head(40))


# %%
# Step 9: Build theme-specific CSV tables
# These are easier to open directly while writing results chapters.

theme_file_map = {
    "Respondent Profile": "01_respondent_profile_tables.csv",
    "General Public: Awareness and Access": "02_general_public_awareness_access_tables.csv",
    "Women Empowerment and Panchayat Participation": "03_women_empowerment_panchayat_tables.csv",
    "Challenges and Constraints": "04_challenges_constraints_tables.csv",
    "Traditional vs Formal Governance": "05_traditional_vs_formal_governance_tables.csv",
    "ICT and Digital Access": "06_ict_digital_access_tables.csv",
    "Agriculture and Livelihood": "07_agriculture_livelihood_tables.csv",
    "Government Officials Perspective": "08_government_officials_tables.csv",
    "Mahila Mukhiya Perspective": "09_mahila_mukhiya_tables.csv",
    "Traditional Leader Perspective": "10_traditional_leader_tables.csv",
    "Women Representative Perspective": "11_women_representative_tables.csv",
    "Other": "12_other_tables.csv",
}

for theme, filename in theme_file_map.items():
    theme_rows = all_descriptive_results[all_descriptive_results["theme"] == theme]
    if len(theme_rows) > 0:
        theme_rows.to_csv(OUTPUT_DIR / filename, index=False)


# %%
# Step 10: Create a compact Markdown summary for quick reading
# This is not a final thesis narrative. It is a high-level guide to the tables.

summary_lines = [
    "# Descriptive Results Summary",
    "",
    "This folder contains descriptive result tables generated from cleaned survey data.",
    "",
    "Use `all_descriptive_results.csv` as the master table.",
    "Use `table_index.csv` to identify which table belongs to which question.",
    "Use `question_level_summary.csv` for quick top-line findings.",
    "",
    "For `multi_response` rows, percentages may exceed 100 within a question because one respondent can contribute to multiple categories.",
    "",
    "## Themes",
]

for theme, count in table_index["theme"].value_counts().sort_index().items():
    summary_lines.append(f"- {theme}: {count} question tables")

summary_lines.extend(["", "## Top-Line Question Summary", ""])

for _, row in question_level_summary.head(30).iterrows():
    summary_lines.append(
        f"- {row['respondent_group']} Q{row['question_no']}: {row['top_answer']} "
        f"({row['top_count']}/{row['denominator_n']}, {row['top_percent']}%)."
    )

(OUTPUT_DIR / "descriptive_results_summary.md").write_text(
    "\n".join(summary_lines),
    encoding="utf-8",
)


# %%
# Step 11: Save master outputs
# CSV files are easy to inspect in Excel, VS Code, or Python.

all_descriptive_results.to_csv(OUTPUT_DIR / "all_descriptive_results.csv", index=False)
question_level_summary.to_csv(OUTPUT_DIR / "question_level_summary.csv", index=False)
table_index.to_csv(OUTPUT_DIR / "table_index.csv", index=False)

# Optional consolidated Excel workbook.
# If the environment lacks an Excel writer, CSV outputs above are still complete.
excel_output_path = OUTPUT_DIR / "descriptive_results_workbook.xlsx"
try:
    with pd.ExcelWriter(excel_output_path) as writer:
        table_index.to_excel(writer, sheet_name="Table Index", index=False)
        question_level_summary.to_excel(writer, sheet_name="Question Summary", index=False)
        all_descriptive_results.to_excel(writer, sheet_name="All Results", index=False)
        multi_response_results.to_excel(writer, sheet_name="Multi Response", index=False)
        single_response_results.to_excel(writer, sheet_name="Single Response", index=False)
    print(f"Excel workbook saved: {excel_output_path}")
except Exception as error:
    print("Excel workbook could not be written; CSV outputs were saved.")
    print(f"Excel writer error: {error}")

print("Saved descriptive results to:")
print(OUTPUT_DIR)
