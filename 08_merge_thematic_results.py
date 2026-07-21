# %%
# Step 8: Merge thematic coding results into final descriptive outputs
# This script integrates the thematic frequency tables produced by
# 07_thematic_coding.py into the main analysis results so they appear
# in reports, Excel workbooks, and the GUI.

from pathlib import Path
import re
import sys

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from IPython.display import display
except ImportError:
    display = print


PROJECT_DIR = Path(__file__).resolve().parent
DESC_DIR = PROJECT_DIR / "outputs" / "descriptive_results"
VALIDATION_DIR = PROJECT_DIR / "outputs" / "validation"
THEMATIC_DIR = PROJECT_DIR / "outputs" / "thematic_coding"

RESULTS_PATH = DESC_DIR / "all_descriptive_results.csv"
QLS_PATH = DESC_DIR / "question_level_summary.csv"
TABLE_INDEX_PATH = DESC_DIR / "table_index.csv"
THEME_FREQ_PATH = THEMATIC_DIR / "thematic_frequencies.csv"
VALIDATION_PATH = VALIDATION_DIR / "validation_status_summary.csv"


# %%
# Step 1: Load data

results = pd.read_csv(RESULTS_PATH)
qls = pd.read_csv(QLS_PATH)
table_index = pd.read_csv(TABLE_INDEX_PATH)
theme_freq = pd.read_csv(THEME_FREQ_PATH)

print(f"Loaded {len(results):,} descriptive result rows")
print(f"Loaded {len(theme_freq):,} thematic frequency rows")


# %%
# Step 2: Theme lookup helper
# Use the theme assigned to the original question in table_index when available.

def lookup_theme(group, q_no):
    """Return the theme from the original (non-thematic) table_index row."""
    match = table_index[
        (table_index["respondent_group"] == group)
        & (table_index["question_no"] == float(q_no))
        & (~table_index["result_type"].isin(["thematic", "raw_open_ended"]))
    ]
    if len(match) > 0:
        return match.iloc[0]["theme"]
    return "Women Empowerment and Panchayat Participation"


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    return text[:60]


# %%
# Step 3: Build thematic result rows

thematic_result_rows = []

for _, row in theme_freq.iterrows():
    group = row["respondent_group"]
    q_no = row["question_no"]
    question = row["question"]
    theme = row["theme"]
    count = row["count"]
    denom = row["denominator_n"]
    pct = row["percent_of_respondents"]

    table_id = f"thematic_{slugify(group)}_q{int(q_no)}_{slugify(question[:30])}"
    assigned_theme = lookup_theme(group, q_no)

    thematic_result_rows.append({
        "table_id": table_id,
        "theme": assigned_theme,
        "result_type": "thematic",
        "respondent_group": group,
        "question_no": float(q_no),
        "section": "",
        "particular": "",
        "question": question,
        "answer": theme,
        "answer_code": slugify(theme),
        "count": count,
        "denominator_n": denom,
        "percent_of_respondents": pct,
    })

thematic_df = pd.DataFrame(thematic_result_rows)

print("\nSample thematic result rows:")
display(thematic_df.head())


# %%
# Step 4: Identify existing fragmented rows to replace
# For each question that now has thematic coding, we mark the old fragmented rows
# as "raw_open_ended" so they remain available but are not the primary result.

coded_questions = set(zip(theme_freq["respondent_group"], theme_freq["question_no"]))

# Rename existing result_type for coded questions to keep raw data accessible
mask_replace = results.apply(
    lambda r: (r["respondent_group"], r["question_no"]) in coded_questions,
    axis=1,
)
results.loc[mask_replace, "result_type"] = "raw_open_ended"

print(f"\nMarked {mask_replace.sum():,} existing rows as 'raw_open_ended'")


# %%
# Step 5: Append thematic rows and save

combined_results = pd.concat([results, thematic_df], ignore_index=True)
combined_results = combined_results.sort_values(["theme", "respondent_group", "question_no", "result_type"])
combined_results.to_csv(DESC_DIR / "all_descriptive_results.csv", index=False)

print(f"\nSaved combined results: {len(combined_results):,} rows")


# %%
# Step 6: Update question-level summary
# Add one row per thematic question

qls_thematic_rows = []
for (group, q_no, question), q_df in theme_freq.groupby(["respondent_group", "question_no", "question"]):
    assigned_theme = lookup_theme(group, q_no)
    table_id = f"thematic_{slugify(group)}_q{int(q_no)}_{slugify(question[:30])}"
    top_row = q_df.sort_values("count", ascending=False).iloc[0]
    qls_thematic_rows.append({
        "table_id": table_id,
        "theme": assigned_theme,
        "result_type": "thematic",
        "respondent_group": group,
        "question_no": float(q_no),
        "question": question,
        "denominator_n": int(q_df["denominator_n"].iloc[0]),
        "number_of_answer_categories": q_df["theme"].nunique(),
        "top_answer": top_row["theme"],
        "top_count": int(top_row["count"]),
        "top_percent": top_row["percent_of_respondents"],
        "note": "Thematic coding of open-ended responses",
    })

qls_thematic = pd.DataFrame(qls_thematic_rows)

# Mark old raw open-ended rows in QLS for coded questions
qls["is_coded_thematically"] = qls.apply(
    lambda r: (r["respondent_group"], r["question_no"]) in coded_questions,
    axis=1,
)
if "note" not in qls.columns:
    qls["note"] = ""
qls.loc[qls["is_coded_thematically"], "note"] = (
    qls.loc[qls["is_coded_thematically"], "note"].fillna("") + " | Thematic coding available"
)
qls["note"] = qls["note"].str.strip(" |")
qls = qls.drop(columns=["is_coded_thematically"])

qls_combined = pd.concat([qls, qls_thematic], ignore_index=True)
qls_combined = qls_combined.sort_values(["theme", "respondent_group", "question_no"])
qls_combined.to_csv(DESC_DIR / "question_level_summary.csv", index=False)

print(f"Saved combined question-level summary: {len(qls_combined):,} rows")


# %%
# Step 7: Update table index

table_index_thematic_rows = []
for _, row in qls_thematic.iterrows():
    q_df = theme_freq[
        (theme_freq["respondent_group"] == row["respondent_group"])
        & (theme_freq["question_no"] == row["question_no"])
    ]
    table_index_thematic_rows.append({
        "table_id": row["table_id"],
        "theme": row["theme"],
        "result_type": "thematic",
        "respondent_group": row["respondent_group"],
        "question_no": row["question_no"],
        "question": row["question"],
        "denominator_n": row["denominator_n"],
        "answer_rows": row["number_of_answer_categories"],
        "total_count": int(q_df["count"].sum()),
        "interpretation_note": "Thematic coding of open-ended responses. Percentages are of respondents.",
    })

table_index_thematic = pd.DataFrame(table_index_thematic_rows)
table_index_combined = pd.concat([table_index, table_index_thematic], ignore_index=True)
table_index_combined = table_index_combined.sort_values(["theme", "respondent_group", "question_no"])
table_index_combined.to_csv(DESC_DIR / "table_index.csv", index=False)

print(f"Saved combined table index: {len(table_index_combined):,} rows")


# %%
# Step 8: Update validation status summary note for fragmented questions
# The per-question action list is updated by 10_validate_results.py when it runs.
# If validation has already run, append the thematic-coding note; otherwise 10
# will generate it automatically because it reads the thematic outputs.

if VALIDATION_PATH.exists():
    validation = pd.read_csv(VALIDATION_PATH)
    frag_row = validation[validation["check"] == "Highly fragmented open-ended questions"]
    if len(frag_row) > 0:
        n_unique_coded = len(coded_questions)
        validation.loc[validation["check"] == "Highly fragmented open-ended questions", "note"] = (
            f"{frag_row.iloc[0]['note'].split(';')[0]}; {n_unique_coded} key questions thematically coded "
            f"(see outputs/thematic_coding/review/thematic_coding_review.xlsx)"
        )
    validation.to_csv(VALIDATION_DIR / "validation_status_summary.csv", index=False)
    print("\nUpdated validation status summary.")
else:
    print("\nValidation summary not present yet; step 10 will generate it.")

print("\nThematic results integrated successfully.")
