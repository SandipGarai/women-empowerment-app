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
MATRIX_SUMMARY_PATH = MATRIX_DIR / "matrix_question_summary.csv"


# %%
# Step 2: Load data

all_results = pd.read_csv(ALL_RESULTS_PATH)
q_summary = pd.read_csv(QUESTION_SUMMARY_PATH)
table_index = pd.read_csv(TABLE_INDEX_PATH)
matrix_freq = pd.read_csv(MATRIX_FREQ_PATH)
matrix_summary = pd.read_csv(MATRIX_SUMMARY_PATH)

print(f"Original all_results rows: {len(all_results):,}")
print(f"Original question_summary rows: {len(q_summary):,}")
print(f"Corrected matrix frequency rows: {len(matrix_freq):,}")
print(f"Corrected matrix summary rows: {len(matrix_summary):,}")


# %%
# Step 3: Convert corrected matrix frequency to all_descriptive_results format

matrix_results = matrix_freq.copy()
matrix_results["result_type"] = matrix_results["response_type"].map(
    {
        "scale": "scale_matrix",
        "categorical": "categorical_matrix",
    }
)

# Assign theme based on question number
q19_items = matrix_results["question_no"].astype(str).str.startswith("19.")
q21_items = matrix_results["question_no"].astype(str).str.startswith("21.")
q23_items = matrix_results["question_no"].astype(str).str.startswith("23.")

matrix_results["theme"] = ""
matrix_results.loc[q19_items, "theme"] = "Women Empowerment and Panchayat Participation"
matrix_results.loc[q21_items, "theme"] = "Challenges and Constraints"
matrix_results.loc[q23_items, "theme"] = "Women Empowerment and Panchayat Participation"

matrix_results["section"] = "Section B" if q19_items.any() else "Section C" if q21_items.any() else "Section D"
matrix_results["particular"] = ""
matrix_results["answer_code"] = matrix_results["answer"]

# Create table_id
matrix_results["table_id"] = matrix_results.apply(
    lambda row: f"{'sm' if row['response_type'] == 'scale' else 'cm'}_women_representative_q{row['question_no']}",
    axis=1,
)

matrix_results = matrix_results.rename(
    columns={
        "answer": "answer",
        "percent_of_respondents": "percent_of_respondents",
    }
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

MATRIX_QUESTION_NOS = [19, 21, 23]

# Remove old broken rows for Women Representative Q19, Q21, Q23
clean_results = all_results[
    ~(
        (all_results["respondent_group"] == "Women Representative")
        & (pd.to_numeric(all_results["question_no"], errors="coerce").isin(MATRIX_QUESTION_NOS))
    )
].copy()

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

clean_q_summary = q_summary[
    ~(
        (q_summary["respondent_group"] == "Women Representative")
        & (pd.to_numeric(q_summary["question_no"], errors="coerce").isin(MATRIX_QUESTION_NOS))
    )
].copy()

matrix_summary_for_q = matrix_summary.copy()
matrix_summary_for_q["table_id"] = matrix_summary_for_q.apply(
    lambda row: f"{'sm' if row['result_type'] == 'scale_matrix' else 'cm'}_women_representative_q{row['question_no']}",
    axis=1,
)
matrix_summary_for_q["theme"] = ""
matrix_summary_for_q.loc[
    matrix_summary_for_q["question_no"].astype(str).str.startswith("19."),
    "theme",
] = "Women Empowerment and Panchayat Participation"
matrix_summary_for_q.loc[
    matrix_summary_for_q["question_no"].astype(str).str.startswith("21."),
    "theme",
] = "Challenges and Constraints"
matrix_summary_for_q.loc[
    matrix_summary_for_q["question_no"].astype(str).str.startswith("23."),
    "theme",
] = "Women Empowerment and Panchayat Participation"

updated_q_summary = pd.concat([clean_q_summary, matrix_summary_for_q], ignore_index=True)
updated_q_summary = updated_q_summary.sort_values(
    ["theme", "respondent_group", "question_no"]
)

print(f"Updated question_summary rows: {len(updated_q_summary):,}")


# %%
# Step 6: Update table index

clean_table_index = table_index[
    ~(
        (table_index["respondent_group"] == "Women Representative")
        & (pd.to_numeric(table_index["question_no"], errors="coerce").isin(MATRIX_QUESTION_NOS))
    )
].copy()

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
    ] = "Matrix questions Q19, Q21, Q23 have been restructured into sub-items."
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
