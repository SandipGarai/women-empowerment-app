# %%
# Step 1: Import libraries and define paths
# This script restructures matrix/multi-part questions in the Women Representative sheet.
# Q19, Q21, Q23 each contain several sub-items stored as separate rows with the same Question No.
# We extract the sub-items, assign new question numbers (e.g., 19.1, 19.2), and produce clean summaries.

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

analysis_rows = pd.read_csv(CLEANED_ANALYSIS_PATH)
print(f"Loaded {len(analysis_rows):,} cleaned analysis rows")


# %%
# Step 3: Helper functions

def normalize_text(value):
    """Clean text for matching."""
    text = "" if pd.isna(value) else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_sub_item(question_text, question_no):
    """Extract the sub-item label from a matrix question text."""
    # Keep original whitespace for regex matching
    text = str(question_text)

    # Q19 and Q21: sub-item is after a bullet "●" and optional tab/space
    if question_no in (19, 21):
        match = re.search(r"[\n\r]+\s*●\s*(.+?)(?:\.|\s*)$", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback bullet variants
        match = re.search(r"[\n\r]+\s*•\s*(.+?)(?:\.|\s*)$", text, re.DOTALL)
        if match:
            return match.group(1).strip()

    # Q23: sub-item is after letter label "a.", "b.", etc. (note: data uses period, not parenthesis)
    if question_no == 23:
        # Match letter label and capture until question mark
        match = re.search(r"[\n\r]+\s*[a-d]\.\s*(.+?\?)", text)
        if match:
            return match.group(1).strip()
        # Fallback: capture "Your ... ?"
        match = re.search(r"(Your .+?\?)", text)
        if match:
            return match.group(1).strip()

    # Last resort: return the full cleaned text
    return normalize_text(text)


def to_numeric_scale(value):
    """Convert response to numeric scale value if possible."""
    text = str(value).strip()
    # Remove decimals like "5.0"
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".")[0]
    if text.isdigit():
        return int(text)
    return None


# %%
# Step 4: Identify matrix question rows

MATRIX_QUESTIONS = {
    19: {
        "base_label": "Involvement in activities",
        "scale": (1, 5),
        "response_type": "scale",
    },
    21: {
        "base_label": "Rate challenges",
        "scale": (1, 5),
        "response_type": "scale",
    },
    23: {
        "base_label": "Change since becoming representative",
        "scale": None,
        "response_type": "categorical",
    },
}

matrix_rows = analysis_rows[
    (analysis_rows["respondent_group"] == "Women Representative")
    & (analysis_rows["Question No"].isin(MATRIX_QUESTIONS.keys()))
].copy()

print(f"Found {len(matrix_rows)} Women Representative matrix rows")


# %%
# Step 5: Extract sub-items and assign new question numbers

matrix_rows["sub_item"] = matrix_rows.apply(
    lambda row: extract_sub_item(row["Question"], row["Question No"]),
    axis=1,
)

# Sort sub-items in original order of appearance to assign stable suffix numbers
sub_item_order = {}
for q_no in MATRIX_QUESTIONS.keys():
    q_rows = matrix_rows[matrix_rows["Question No"] == q_no]
    sub_items = q_rows["sub_item"].drop_duplicates().tolist()
    sub_item_order[q_no] = {label: i + 1 for i, label in enumerate(sub_items)}

matrix_rows["sub_item_suffix"] = matrix_rows.apply(
    lambda row: sub_item_order[row["Question No"]][row["sub_item"]],
    axis=1,
)
matrix_rows["new_question_no"] = matrix_rows.apply(
    lambda row: f"{int(row['Question No'])}.{row['sub_item_suffix']}",
    axis=1,
)
matrix_rows["new_question_label"] = matrix_rows.apply(
    lambda row: f"{MATRIX_QUESTIONS[row['Question No']]['base_label']}: {row['sub_item']}",
    axis=1,
)

# Show extracted sub-items
print("\nExtracted sub-items:")
for q_no in MATRIX_QUESTIONS.keys():
    print(f"\nQ{q_no}:")
    sub_df = matrix_rows[matrix_rows["Question No"] == q_no][["new_question_no", "new_question_label"]].drop_duplicates()
    for _, row in sub_df.iterrows():
        print(f"  {row['new_question_no']}: {row['new_question_label']}")


# %%
# Step 6: Validate scale responses and flag invalid entries

matrix_rows["scale_value"] = matrix_rows["response_clean"].apply(to_numeric_scale)

# For scale questions, identify non-numeric or out-of-range responses
scale_questions = [q_no for q_no, info in MATRIX_QUESTIONS.items() if info["response_type"] == "scale"]
invalid_scale = matrix_rows[
    (matrix_rows["Question No"].isin(scale_questions))
    & (
        matrix_rows["scale_value"].isna()
        | (matrix_rows["scale_value"] < 1)
        | (matrix_rows["scale_value"] > 5)
    )
].copy()

if len(invalid_scale) > 0:
    print(f"\n⚠️ Found {len(invalid_scale)} invalid scale responses (will be excluded from scale stats):")
    print(invalid_scale[["new_question_no", "new_question_label", "respondent_id", "response_clean"]].to_string(index=False))
else:
    print("\n✅ All scale responses are valid (1-5)")


# %%
# Step 7: Build corrected frequency tables for each sub-item

frequency_rows = []

for (q_no, sub_item, new_q_no, new_label), group in matrix_rows.groupby(
    ["Question No", "sub_item", "new_question_no", "new_question_label"], dropna=False
):
    info = MATRIX_QUESTIONS[q_no]
    respondents = group["respondent_id"].nunique()

    if info["response_type"] == "scale":
        # For scale: report each numeric value
        valid_group = group[group["scale_value"].notna()].copy()
        value_counts = valid_group["scale_value"].value_counts().sort_index()
        for value, count in value_counts.items():
            frequency_rows.append({
                "respondent_group": "Women Representative",
                "original_question_no": q_no,
                "question_no": new_q_no,
                "question": new_label,
                "response_type": "scale",
                "answer": str(int(value)),
                "count": count,
                "denominator_n": respondents,
                "percent_of_respondents": round(count / respondents * 100, 2),
            })
    else:
        # Categorical
        value_counts = group["response_clean"].value_counts()
        for value, count in value_counts.items():
            frequency_rows.append({
                "respondent_group": "Women Representative",
                "original_question_no": q_no,
                "question_no": new_q_no,
                "question": new_label,
                "response_type": "categorical",
                "answer": str(value),
                "count": count,
                "denominator_n": respondents,
                "percent_of_respondents": round(count / respondents * 100, 2),
            })

matrix_frequency = pd.DataFrame(frequency_rows)
matrix_frequency = matrix_frequency.sort_values(["original_question_no", "question_no", "count"], ascending=[True, True, False])

print("\nCorrected matrix frequency tables:")
display(matrix_frequency.head(30))


# %%
# Step 8: Calculate scale statistics for Q19 and Q21

scale_stats_rows = []

for q_no in scale_questions:
    q_data = matrix_rows[matrix_rows["Question No"] == q_no]
    for (sub_item, new_q_no, new_label), group in q_data.groupby(
        ["sub_item", "new_question_no", "new_question_label"], dropna=False
    ):
        valid = group[group["scale_value"].notna()]["scale_value"]
        if len(valid) == 0:
            continue
        scale_stats_rows.append({
            "respondent_group": "Women Representative",
            "original_question_no": q_no,
            "question_no": new_q_no,
            "question": new_label,
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
matrix_scale_stats = matrix_scale_stats.sort_values(["original_question_no", "question_no"])

print("\nScale statistics (mean, SD, high/low percentages):")
display(matrix_scale_stats)


# %%
# Step 9: Build a corrected question-level summary

summary_rows = []

# For scale questions: use mean as the "top" indicator
for _, row in matrix_scale_stats.iterrows():
    summary_rows.append({
        "respondent_group": "Women Representative",
        "result_type": "scale_matrix",
        "question_no": row["question_no"],
        "question": row["question"],
        "denominator_n": row["n_total"],
        "number_of_answer_categories": 5,
        "top_answer": f"Mean = {row['mean']} (SD = {row['std']})",
        "top_count": row["n_valid"],
        "top_percent": row["percent_high_4_5"],
        "note": "Scale 1-5; % high = rated 4 or 5",
    })

# For categorical questions: use the most common category
for (q_no, new_q_no, new_label), group_df in matrix_frequency[
    matrix_frequency["response_type"] == "categorical"
].groupby(["original_question_no", "question_no", "question"], dropna=False):
    top = group_df.sort_values("count", ascending=False).iloc[0]
    summary_rows.append({
        "respondent_group": "Women Representative",
        "result_type": "categorical_matrix",
        "question_no": new_q_no,
        "question": new_label,
        "denominator_n": top["denominator_n"],
        "number_of_answer_categories": len(group_df),
        "top_answer": top["answer"],
        "top_count": top["count"],
        "top_percent": top["percent_of_respondents"],
        "note": "",
    })

matrix_summary = pd.DataFrame(summary_rows)
matrix_summary = matrix_summary.sort_values(["question_no"])

print("\nCorrected question-level summary:")
display(matrix_summary)


# %%
# Step 10: Save outputs

matrix_rows.to_csv(OUTPUT_DIR / "matrix_long_corrected.csv", index=False)
matrix_frequency.to_csv(OUTPUT_DIR / "matrix_frequency_corrected.csv", index=False)
matrix_scale_stats.to_csv(OUTPUT_DIR / "matrix_scale_statistics.csv", index=False)
matrix_summary.to_csv(OUTPUT_DIR / "matrix_question_summary.csv", index=False)
invalid_scale.to_csv(OUTPUT_DIR / "matrix_invalid_scale_responses.csv", index=False)

print("\nSaved corrected matrix outputs to:")
print(OUTPUT_DIR)
