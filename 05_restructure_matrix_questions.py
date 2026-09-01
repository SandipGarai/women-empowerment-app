# %%
# Step 1: Import libraries and define paths
#
# This script groups the "matrix" questions (batteries of sub-items that share a
# common stem) into analysable blocks and produces scale statistics for them.
#
# IMPORTANT CHANGE (Sept 2026 data update):
# In the earlier workbook every sub-item of a matrix shared ONE Question No
# (all involvement items were Q19, all challenges were Q21, etc.), so this
# script had to SPLIT those rows apart. In the current workbook each sub-item
# already has its own Question No (involvement = Q19-Q22, challenges = Q24-Q31,
# change-since = Q33-Q36). So the script no longer splits: it GROUPS.
#
# To avoid breaking again the next time questions are renumbered, blocks are now
# detected from the QUESTION TEXT (the shared stem before the colon), not from
# hard-coded question numbers.

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
CLEANED_DIR = PROJECT_DIR / "outputs" / "cleaned"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "matrix_corrected"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_ANALYSIS_PATH = CLEANED_DIR / "cleaned_analysis_responses.csv"


# %%
# Step 2: Load cleaned analysis responses

analysis_rows = pd.read_csv(CLEANED_ANALYSIS_PATH, dtype={"Question No": str})
print(f"Loaded {len(analysis_rows):,} cleaned analysis rows")


# %%
# Step 3: Define the matrix blocks by their shared question stem
#
# "stem_pattern" is matched (case-insensitively) against the start of the
# question text. Everything after the stem is treated as the sub-item label.

MATRIX_GROUPS = [
    {
        "group_id": "wr_involvement",
        "respondent_group": "Women Representative",
        "stem_pattern": r"on a scale of 1\s*-\s*5,?\s*involvement in activities\s*:",
        "base_label": "Involvement in activities",
        "response_type": "scale",
        "scale_min": 1,
        "scale_max": 5,
        "section": "Section B",
        "theme": "Women Empowerment and Panchayat Participation",
    },
    {
        "group_id": "wr_challenges",
        "respondent_group": "Women Representative",
        "stem_pattern": r"rate challenges on scale 1\s*-\s*5,?\s*rate the following challenges you face\s*:",
        "base_label": "Rate challenges",
        "response_type": "scale",
        "scale_min": 1,
        "scale_max": 5,
        "section": "Section C",
        "theme": "Challenges and Constraints",
    },
    {
        "group_id": "wr_change_since",
        "respondent_group": "Women Representative",
        "stem_pattern": r"change since becoming representative,?\s*do you feel there has been a change in\s*:",
        "base_label": "Change since becoming representative",
        "response_type": "categorical",
        "scale_min": None,
        "scale_max": None,
        "section": "Section D",
        "theme": "Women Empowerment and Panchayat Participation",
    },
]


# %%
# Step 4: Helper functions

def normalize_text(value):
    """Collapse whitespace and strip."""
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"\s+", " ", text).strip()


def extract_sub_item(question_text, stem_pattern):
    """Return the sub-item label, i.e. the part of the question after the stem."""
    text = normalize_text(question_text)

    match = re.match(stem_pattern, text, flags=re.IGNORECASE)
    if match:
        text = text[match.end():].strip()

    # Drop a leading enumerator such as "a.", "b)", "1." or a bullet.
    text = re.sub(r"^\s*(?:[a-z]\s*[\.\)]|\d+\s*[\.\)]|[\u2022\u25cf\u25aa-])\s*", "", text, flags=re.IGNORECASE)

    # If the sub-item is a question, cut off the answer options that follow it.
    if "?" in text:
        text = text.split("?")[0].strip() + "?"

    # Otherwise drop a trailing full stop.
    text = text.rstrip(". ").strip()

    return text


def to_numeric_scale(value):
    """Convert a response to an integer scale value, or None."""
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".")[0]
    return int(text) if text.isdigit() else None


# %%
# Step 5: Tag every cleaned row with the matrix block it belongs to (if any)

analysis_rows["question_normalized"] = analysis_rows["Question"].map(normalize_text)

matched_frames = []

for group in MATRIX_GROUPS:
    mask = (
        (analysis_rows["respondent_group"] == group["respondent_group"])
        & analysis_rows["question_normalized"].str.contains(
            group["stem_pattern"], case=False, regex=True, na=False
        )
    )
    block = analysis_rows[mask].copy()

    if block.empty:
        # Loud failure instead of a confusing crash 20 lines later.
        print(
            f"WARNING: matrix block '{group['group_id']}' matched 0 rows. "
            f"The question wording for '{group['base_label']}' may have changed "
            f"in the workbook. Update its stem_pattern in Step 3."
        )
        continue

    block["group_id"] = group["group_id"]
    block["base_label"] = group["base_label"]
    block["response_type"] = group["response_type"]
    block["section"] = group["section"]
    block["theme"] = group["theme"]
    block["sub_item"] = block["Question"].map(
        lambda q, p=group["stem_pattern"]: extract_sub_item(q, p)
    )
    matched_frames.append(block)

if not matched_frames:
    raise SystemExit(
        "No matrix blocks matched any rows. Check that 02_clean_and_code_surveys.py "
        "has been run against the current Surveys.xlsx, and that the question stems "
        "in Step 3 still match the workbook wording."
    )

matrix_rows = pd.concat(matched_frames, ignore_index=True)

print(f"\nMatched {len(matrix_rows):,} matrix rows across {matrix_rows['group_id'].nunique()} blocks")
print(matrix_rows.groupby("group_id")["Question No"].nunique().to_string())


# %%
# Step 6: Assign stable sub-item numbers within each block

matrix_rows["question_no_base"] = pd.to_numeric(
    matrix_rows["Question No"].str.extract(r"(\d+)")[0], errors="coerce"
)

sub_item_suffix = {}
for group_id, group_df in matrix_rows.groupby("group_id", sort=False):
    ordered = (
        group_df.sort_values("question_no_base")[["Question No", "sub_item"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    for position, row in ordered.iterrows():
        sub_item_suffix[(group_id, row["Question No"])] = position + 1

matrix_rows["sub_item_suffix"] = [
    sub_item_suffix[(g, q)] for g, q in zip(matrix_rows["group_id"], matrix_rows["Question No"])
]

# The workbook now numbers each sub-item itself, so the real Question No is the
# question number used in all outputs. block_item_no is kept for readable labels
# such as "Involvement 1 of 4".
matrix_rows["question_no"] = matrix_rows["Question No"]
matrix_rows["block_item_no"] = matrix_rows["sub_item_suffix"]
matrix_rows["question_label"] = matrix_rows["base_label"] + ": " + matrix_rows["sub_item"]

print("\nDetected sub-items:")
for group_id, group_df in matrix_rows.groupby("group_id", sort=False):
    print(f"\n{group_id}:")
    listing = group_df[["question_no", "question_label"]].drop_duplicates().sort_values("question_no", key=lambda s: s.astype(int))
    for _, row in listing.iterrows():
        print(f"  Q{row['question_no']}: {row['question_label']}")


# %%
# Step 7: Validate scale responses

matrix_rows["scale_value"] = matrix_rows["response_clean"].apply(to_numeric_scale)

scale_mask = matrix_rows["response_type"] == "scale"
invalid_scale = matrix_rows[
    scale_mask
    & (
        matrix_rows["scale_value"].isna()
        | (matrix_rows["scale_value"] < 1)
        | (matrix_rows["scale_value"] > 5)
    )
].copy()

if len(invalid_scale) > 0:
    print(f"\nWARNING: {len(invalid_scale)} invalid scale responses (excluded from scale statistics):")
    print(
        invalid_scale[["question_no", "question_label", "respondent_id", "response_clean"]]
        .to_string(index=False)
    )
else:
    print("\nAll scale responses are valid (1-5)")


# %%
# Step 8: Frequency tables per sub-item

frequency_rows = []

group_keys = ["group_id", "respondent_group", "question_no", "question_label", "response_type", "section", "theme"]

for keys, group in matrix_rows.groupby(group_keys, dropna=False):
    group_id, respondent_group, question_no, question_label, response_type, section, theme = keys
    respondents = group["respondent_id"].nunique()

    if response_type == "scale":
        valid = group[group["scale_value"].notna()]
        counts = valid["scale_value"].value_counts().sort_index()
        answers = [(str(int(value)), count) for value, count in counts.items()]
    else:
        counts = group["response_clean"].value_counts()
        answers = [(str(value), count) for value, count in counts.items()]

    for answer, count in answers:
        frequency_rows.append({
            "group_id": group_id,
            "respondent_group": respondent_group,
            "question_no": question_no,
            "question": question_label,
            "section": section,
            "theme": theme,
            "response_type": response_type,
            "answer": answer,
            "count": count,
            "denominator_n": respondents,
            "percent_of_respondents": round(count / respondents * 100, 2),
        })

matrix_frequency = pd.DataFrame(frequency_rows)
matrix_frequency["_sort"] = pd.to_numeric(matrix_frequency["question_no"].str.extract(r"(\d+)")[0], errors="coerce")
matrix_frequency = matrix_frequency.sort_values(["_sort", "count"], ascending=[True, False]).drop(columns="_sort")

print("\nMatrix frequency tables:")
display(matrix_frequency.head(30))


# %%
# Step 9: Scale statistics for the 1-5 blocks

scale_stats_rows = []

for keys, group in matrix_rows[scale_mask].groupby(group_keys, dropna=False):
    group_id, respondent_group, question_no, question_label, response_type, section, theme = keys
    valid = group[group["scale_value"].notna()]["scale_value"]
    if len(valid) == 0:
        continue
    scale_stats_rows.append({
        "group_id": group_id,
        "respondent_group": respondent_group,
        "question_no": question_no,
        "question": question_label,
        "section": section,
        "theme": theme,
        "n_valid": len(valid),
        "n_total": group["respondent_id"].nunique(),
        "mean": round(valid.mean(), 2),
        "std": round(valid.std(), 2),
        "min": int(valid.min()),
        "max": int(valid.max()),
        "percent_high_4_5": round(((valid >= 4).sum() / len(valid)) * 100, 2),
        "percent_low_1_2": round(((valid <= 2).sum() / len(valid)) * 100, 2),
    })

matrix_scale_stats = pd.DataFrame(scale_stats_rows)
if not matrix_scale_stats.empty:
    matrix_scale_stats["_sort"] = pd.to_numeric(
        matrix_scale_stats["question_no"].str.extract(r"(\d+)")[0], errors="coerce"
    )
    matrix_scale_stats = matrix_scale_stats.sort_values("_sort").drop(columns="_sort")

print("\nScale statistics (mean, SD, high/low percentages):")
display(matrix_scale_stats)


# %%
# Step 10: Question-level summary

summary_rows = []

for _, row in matrix_scale_stats.iterrows():
    summary_rows.append({
        "respondent_group": row["respondent_group"],
        "result_type": "scale_matrix",
        "question_no": row["question_no"],
        "question": row["question"],
        "section": row["section"],
        "theme": row["theme"],
        "denominator_n": row["n_total"],
        "number_of_answer_categories": 5,
        "top_answer": f"Mean = {row['mean']} (SD = {row['std']})",
        "top_count": row["n_valid"],
        "top_percent": row["percent_high_4_5"],
        "note": "Scale 1-5; % high = rated 4 or 5",
    })

categorical_freq = matrix_frequency[matrix_frequency["response_type"] == "categorical"]
for keys, group_df in categorical_freq.groupby(
    ["respondent_group", "question_no", "question", "section", "theme"], dropna=False
):
    respondent_group, question_no, question_label, section, theme = keys
    top = group_df.sort_values("count", ascending=False).iloc[0]
    summary_rows.append({
        "respondent_group": respondent_group,
        "result_type": "categorical_matrix",
        "question_no": question_no,
        "question": question_label,
        "section": section,
        "theme": theme,
        "denominator_n": top["denominator_n"],
        "number_of_answer_categories": len(group_df),
        "top_answer": top["answer"],
        "top_count": top["count"],
        "top_percent": top["percent_of_respondents"],
        "note": "",
    })

matrix_summary = pd.DataFrame(summary_rows)
matrix_summary["_sort"] = pd.to_numeric(matrix_summary["question_no"].str.extract(r"(\d+)")[0], errors="coerce")
matrix_summary = matrix_summary.sort_values("_sort").drop(columns="_sort")

print("\nQuestion-level summary:")
display(matrix_summary)


# %%
# Step 11: Record which questions this script has taken over
#
# Script 06 uses this file to know exactly which rows to replace in the main
# descriptive results, instead of relying on a hard-coded [19, 21, 23] list.

handled_questions = (
    matrix_rows[["respondent_group", "question_no", "group_id", "section", "theme"]]
    .drop_duplicates()
    .sort_values(["respondent_group", "question_no"])
)


# %%
# Step 12: Save outputs

matrix_rows.to_csv(OUTPUT_DIR / "matrix_long_corrected.csv", index=False)
matrix_frequency.to_csv(OUTPUT_DIR / "matrix_frequency_corrected.csv", index=False)
matrix_scale_stats.to_csv(OUTPUT_DIR / "matrix_scale_statistics.csv", index=False)
matrix_summary.to_csv(OUTPUT_DIR / "matrix_question_summary.csv", index=False)
invalid_scale.to_csv(OUTPUT_DIR / "matrix_invalid_scale_responses.csv", index=False)
handled_questions.to_csv(OUTPUT_DIR / "matrix_handled_questions.csv", index=False)

print("\nSaved matrix outputs to:")
print(OUTPUT_DIR)
