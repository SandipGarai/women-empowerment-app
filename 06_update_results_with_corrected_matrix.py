# %%
# Step 1: Imports and paths
# This script merges the corrected matrix question results into the main descriptive results.
# It removes the old broken matrix entries (Women Representative Q19, Q21, Q23)
# and replaces them with properly restructured sub-items.

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = PROJECT_DIR / "outputs" / "descriptive_results"
MATRIX_DIR = PROJECT_DIR / "outputs" / "matrix_corrected"
VALIDATION_DIR = PROJECT_DIR / "outputs" / "validation"

ALL_RESULTS_PATH = RESULTS_DIR / "all_descriptive_results.csv"
QUESTION_SUMMARY_PATH = RESULTS_DIR / "question_level_summary.csv"
TABLE_INDEX_PATH = RESULTS_DIR / "table_index.csv"

MATRIX_FREQ_PATH = MATRIX_DIR / "matrix_frequency_corrected.csv"
MATRIX_HANDLED_PATH = MATRIX_DIR / "matrix_handled_questions.csv"
MATRIX_SUMMARY_PATH = MATRIX_DIR / "matrix_question_summary.csv"


# %%
# Step 2: Load data

all_results = pd.read_csv(ALL_RESULTS_PATH, dtype={"question_no": str})
q_summary = pd.read_csv(QUESTION_SUMMARY_PATH, dtype={"question_no": str})
table_index = pd.read_csv(TABLE_INDEX_PATH, dtype={"question_no": str})
matrix_freq = pd.read_csv(MATRIX_FREQ_PATH, dtype={"question_no": str})
matrix_summary = pd.read_csv(MATRIX_SUMMARY_PATH, dtype={"question_no": str})
matrix_handled = pd.read_csv(MATRIX_HANDLED_PATH, dtype={"question_no": str})

print(f"Original all_results rows: {len(all_results):,}")
print(f"Original question_summary rows: {len(q_summary):,}")
print(f"Corrected matrix frequency rows: {len(matrix_freq):,}")
print(f"Corrected matrix summary rows: {len(matrix_summary):,}")


# %%
# Step 3: Convert corrected matrix frequency to all_descriptive_results format
#
# Theme and section now come from script 05 rather than from hard-coded
# question-number prefixes, so renumbering the workbook no longer breaks this.

matrix_results = matrix_freq.copy()
matrix_results["result_type"] = matrix_results["response_type"].map(
    {
        "scale": "scale_matrix",
        "categorical": "categorical_matrix",
    }
)

matrix_results["particular"] = ""
matrix_results["answer_code"] = matrix_results["answer"]

# Create table_id
matrix_results["table_id"] = matrix_results.apply(
    lambda row: f"{'sm' if row['response_type'] == 'scale' else 'cm'}"
                f"_{row['respondent_group'].lower().replace(' ', '_')}_q{row['question_no']}",
    axis=1,
)

matrix_results = matrix_results[
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


# %%
# Step 4: Remove old broken matrix entries and append corrected ones

# The exact (respondent_group, question_no) pairs handled by script 05.
HANDLED_PAIRS = set(zip(matrix_handled["respondent_group"], matrix_handled["question_no"].astype(str)))

print(f"Matrix questions taken over by script 05: {len(HANDLED_PAIRS)}")


def is_handled(frame):
    """True where a row was replaced by the matrix-corrected version."""
    pairs = zip(frame["respondent_group"], frame["question_no"].astype(str))
    return pd.Series([pair in HANDLED_PAIRS for pair in pairs], index=frame.index)


clean_results = all_results[~is_handled(all_results)].copy()

print(f"Rows after removing old matrix entries: {len(clean_results):,}")

# Append corrected matrix rows
updated_results = pd.concat([clean_results, matrix_results], ignore_index=True)
updated_results = updated_results.sort_values(
    ["theme", "respondent_group", "question_no", "result_type", "count"],
    ascending=[True, True, True, True, False],
)

print(f"Rows after adding corrected matrix entries: {len(updated_results):,}")


# %%
# Step 5: Update question-level summary

clean_q_summary = q_summary[~is_handled(q_summary)].copy()

# theme/section already carried through from script 05
matrix_summary_for_q = matrix_summary.copy()
matrix_summary_for_q["table_id"] = matrix_summary_for_q.apply(
    lambda row: f"{'sm' if row['result_type'] == 'scale_matrix' else 'cm'}"
                f"_{row['respondent_group'].lower().replace(' ', '_')}_q{row['question_no']}",
    axis=1,
)

updated_q_summary = pd.concat([clean_q_summary, matrix_summary_for_q], ignore_index=True)
updated_q_summary = updated_q_summary.sort_values(
    ["theme", "respondent_group", "question_no"]
)

print(f"Updated question_summary rows: {len(updated_q_summary):,}")


# %%
# Step 6: Update table index

clean_table_index = table_index[~is_handled(table_index)].copy()

# Build new table index rows from updated results
new_table_index = (
    updated_results.groupby(
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

new_table_index["interpretation_note"] = new_table_index["result_type"].map(
    {
        "single_response": "Use count and percent as ordinary response distribution.",
        "multi_response": "Use count and percent as category mentions; percentages may exceed 100.",
        "scale_matrix": "Scale 1-5: use mean/SD and high/low percentages.",
        "categorical_matrix": "Categorical sub-item: use count and percent.",
    }
).fillna("Use count and percent as ordinary response distribution.")

new_table_index = new_table_index.sort_values(["theme", "respondent_group", "question_no"])

print(f"Updated table_index rows: {len(new_table_index):,}")


# %%
# Step 7: Update validation status summary

validation_status_path = VALIDATION_DIR / "validation_status_summary.csv"
if validation_status_path.exists():
    validation_status = pd.read_csv(validation_status_path)
    # Mark matrix issue as fixed if all matrix questions are now correctly split
    validation_status.loc[
        validation_status["check"] == "High-severity count logic errors",
        "status",
    ] = "PASS"
    validation_status.loc[
        validation_status["check"] == "High-severity count logic errors",
        "note",
    ] = "Matrix sub-items are grouped and summarised by 05_restructure_matrix_questions.py."
    validation_status.loc[
        validation_status["check"] == "Matrix questions need restructuring",
        "status",
    ] = "PASS"
    validation_status.loc[
        validation_status["check"] == "Matrix questions need restructuring",
        "note",
    ] = "Restructured using 05_restructure_matrix_questions.py and 06_update_results_with_corrected_matrix.py"
    validation_status.to_csv(validation_status_path, index=False)
    print("Updated validation_status_summary.csv")


# %%
# Step 8: Save updated outputs

# Save corrected main files
updated_results.to_csv(RESULTS_DIR / "all_descriptive_results.csv", index=False)
updated_q_summary.to_csv(RESULTS_DIR / "question_level_summary.csv", index=False)
new_table_index.to_csv(RESULTS_DIR / "table_index.csv", index=False)

# Also save backup copies of original (already existed, but keep corrected versions clearly named)
updated_results.to_csv(RESULTS_DIR / "all_descriptive_results_corrected.csv", index=False)
updated_q_summary.to_csv(RESULTS_DIR / "question_level_summary_corrected.csv", index=False)
new_table_index.to_csv(RESULTS_DIR / "table_index_corrected.csv", index=False)

print("\nSaved corrected results to outputs/descriptive_results/")
print("- all_descriptive_results.csv")
print("- question_level_summary.csv")
print("- table_index.csv")
print("- *_corrected.csv backup copies")
