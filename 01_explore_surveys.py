# %%
# Step 1: Import libraries and define file paths
# This script is written in VS Code / ipykernel style.
# Run each # %% cell one by one to explore the survey workbook gradually.

from pathlib import Path
import sys

import pandas as pd

# Windows terminals sometimes default to a legacy encoding.
# UTF-8 keeps Hindi/tribal/local-language responses printable.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    # display gives nicer tables inside VS Code notebooks / ipykernel.
    from IPython.display import display
except ImportError:
    # Plain Python fallback so the script can also be run from the terminal.
    display = print

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# Path to the current project folder.
PROJECT_DIR = Path(__file__).resolve().parent

# Input files supplied for this analysis.
EXCEL_PATH = PROJECT_DIR / "Surveys.xlsx"
SYNOPSIS_PATH = PROJECT_DIR / "Synopsis V6 -.pdf"

# Folder for exploration outputs.
OUTPUT_DIR = PROJECT_DIR / "outputs" / "exploration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# %%
# Step 2: Read the Excel workbook structure
# We first inspect sheet names before loading all data.

excel_file = pd.ExcelFile(EXCEL_PATH)

# Each sheet appears to represent one respondent category.
sheet_names = excel_file.sheet_names
print("Sheets in workbook:")
for sheet_name in sheet_names:
    print(f"- {sheet_name}")


# %%
# Step 3: Load all sheets into a dictionary of DataFrames
# The dictionary key is the sheet/respondent group name.

survey_sheets = {
    sheet_name: pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
    for sheet_name in sheet_names
}

# Show basic dimensions for each sheet.
for sheet_name, df in survey_sheets.items():
    print(f"{sheet_name}: {df.shape[0]} rows x {df.shape[1]} columns")


# %%
# Step 4: Build a workbook overview table
# Metadata columns describe questions; remaining columns are individual respondents.

metadata_columns = ["Question No", "Section", "Particular", "Question"]


def real_respondent_columns(df, metadata_columns):
    """
    Return only the columns that are genuinely respondents.

    Spreadsheets routinely carry phantom trailing columns: one stray character
    far to the right of the data makes pandas invent hundreds of "Unnamed: N"
    columns. Counting those as respondents inflated the General Public sheet
    from 53 to 269 and produced a false validation FAIL, and it also created
    hundreds of empty respondent records in the long-format data.

    A real respondent column has a proper header (not "Unnamed: N") and at
    least one non-blank answer.
    """
    keep = []
    for col in df.columns:
        if col in metadata_columns:
            continue
        if str(col).startswith("Unnamed:"):
            continue
        if df[col].isna().all():
            continue
        keep.append(col)
    return keep

overview_rows = []

for sheet_name, df in survey_sheets.items():
    # Respondent columns are all columns after the standard question metadata fields.
    respondent_columns = real_respondent_columns(df, metadata_columns)

    overview_rows.append(
        {
            "sheet": sheet_name,
            "question_rows": len(df),
            "total_columns": len(df.columns),
            "respondent_columns": len(respondent_columns),
            "first_respondent_column": respondent_columns[0] if respondent_columns else None,
            "last_respondent_column": respondent_columns[-1] if respondent_columns else None,
            "missing_cells_total": int(df.isna().sum().sum()),
        }
    )

workbook_overview = pd.DataFrame(overview_rows)
workbook_overview


# %%
# Step 5: Inspect sections and sample questions
# This helps us understand the questionnaire design before statistical analysis.

for sheet_name, df in survey_sheets.items():
    print("\n" + "=" * 80)
    print(sheet_name)
    print("=" * 80)

    if "Section" in df.columns:
        sections = df["Section"].dropna().astype(str).unique()
        print("Sections:")
        for section in sections:
            print(f"- {section}")

    print("\nFirst 8 question rows:")
    display_columns = [col for col in metadata_columns if col in df.columns]
    display(df[display_columns].head(8))


# %%
# Step 6: Check missing values by sheet and column
# Missingness matters because each row is a question and each response column is a respondent.

missingness_rows = []

for sheet_name, df in survey_sheets.items():
    for column in df.columns:
        missingness_rows.append(
            {
                "sheet": sheet_name,
                "column": column,
                "missing_count": int(df[column].isna().sum()),
                "missing_percent": round(df[column].isna().mean() * 100, 2),
            }
        )

missingness_by_column = pd.DataFrame(missingness_rows)
missingness_by_column.sort_values(
    ["sheet", "missing_count"], ascending=[True, False]
).head(20)


# %%
# Step 7: Convert wide survey sheets into one long-format table
# Long format is easier for frequency tables, plots, group comparisons, and later coding.

long_tables = []

for sheet_name, df in survey_sheets.items():
    respondent_columns = real_respondent_columns(df, metadata_columns)

    # id_vars stay fixed for each question; value_vars become respondent-response rows.
    long_df = df.melt(
        id_vars=metadata_columns,
        value_vars=respondent_columns,
        var_name="respondent_id",
        value_name="response",
    )

    # Add sheet/respondent category so groups can be compared later.
    long_df.insert(0, "respondent_group", sheet_name)

    long_tables.append(long_df)

survey_long = pd.concat(long_tables, ignore_index=True)

# Remove completely blank responses for response-frequency summaries.
survey_long_nonblank = survey_long.dropna(subset=["response"]).copy()

# Mark questions that are likely identifiers or profile descriptors.
# These are useful for sampling context, but they should usually be excluded
# from substantive frequency tables and charts.
profile_keywords = [
    "name",
    "who the mukhiya",
    "village",
    "panchayat",
    "block",
    "district",
]

survey_long_nonblank["is_profile_or_identifier"] = (
    survey_long_nonblank["Question"]
    .astype(str)
    .str.lower()
    .apply(lambda text: any(keyword in text for keyword in profile_keywords))
)

survey_long_analysis = survey_long_nonblank[
    ~survey_long_nonblank["is_profile_or_identifier"]
].copy()

print(f"Long-format rows, including blanks: {len(survey_long):,}")
print(f"Long-format rows, nonblank only: {len(survey_long_nonblank):,}")
print(f"Nonblank rows excluding likely profile/identifier fields: {len(survey_long_analysis):,}")
display(survey_long_analysis.head(10))


# %%
# Step 8: Create initial response frequency tables
# This is a first-pass descriptive count, not yet a final statistical interpretation.

response_frequency = (
    survey_long_analysis.assign(response=lambda x: x["response"].astype(str).str.strip())
    .groupby(["respondent_group", "Question No", "Section", "Particular", "Question", "response"])
    .size()
    .reset_index(name="count")
    .sort_values(["respondent_group", "Question No", "count"], ascending=[True, True, False])
)

display(response_frequency.head(30))


# %%
# Step 9: Identify question rows that may need cleaning or special handling
# Open-ended text, multiple-response answers, and numeric answers often need different analysis.

question_diagnostics = []

for (respondent_group, question_no, question), group_df in survey_long_nonblank.groupby(
    ["respondent_group", "Question No", "Question"], dropna=False
):
    responses = group_df["response"].astype(str).str.strip()

    question_diagnostics.append(
        {
            "respondent_group": respondent_group,
            "question_no": question_no,
            "question": question,
            "nonblank_responses": len(responses),
            "unique_responses": responses.nunique(dropna=True),
            "sample_responses": "; ".join(responses.drop_duplicates().head(5)),
        }
    )

question_diagnostics = pd.DataFrame(question_diagnostics)
question_diagnostics.sort_values(
    ["respondent_group", "unique_responses"], ascending=[True, False]
).head(25)


# %%
# Step 10: Extract a light synopsis context from the PDF
# This is only for orientation. We are not doing a full PDF analysis yet.

if PdfReader is None:
    print("pypdf is not available in this Python environment.")
elif not SYNOPSIS_PATH.exists():
    print("Synopsis PDF not found.")
else:
    reader = PdfReader(SYNOPSIS_PATH)
    synopsis_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    synopsis_context_rows = []

    print(f"Synopsis pages: {len(reader.pages)}")
    print("\nTitle / opening context:")
    print(synopsis_text[:1200])

    # Search for study-design keywords to orient the survey analysis.
    keywords = [
        "objectives",
        "hypothesis",
        "methodology",
        "sample",
        "universe",
        "women empowerment",
        "democratic decentralization",
    ]

    for keyword in keywords:
        location = synopsis_text.lower().find(keyword.lower())
        print(f"{keyword}: {'found at character ' + str(location) if location >= 0 else 'not found'}")

        if location >= 0:
            # Keep a compact context window for audit, not a full PDF extraction.
            start = max(location - 250, 0)
            end = min(location + 1000, len(synopsis_text))
            synopsis_context_rows.append(
                {
                    "keyword": keyword,
                    "character_location": location,
                    "context": synopsis_text[start:end].replace("\n", " ").strip(),
                }
            )

    synopsis_keyword_context = pd.DataFrame(synopsis_context_rows)
    synopsis_keyword_context.to_csv(
        OUTPUT_DIR / "synopsis_keyword_context.csv", index=False
    )


# %%
# Step 11: Save exploration outputs for review
# These files are small checkpoints for the next step of analysis.

workbook_overview.to_csv(OUTPUT_DIR / "workbook_overview.csv", index=False)
missingness_by_column.to_csv(OUTPUT_DIR / "missingness_by_column.csv", index=False)
survey_long.to_csv(OUTPUT_DIR / "survey_long_all_responses.csv", index=False)
survey_long_analysis.to_csv(OUTPUT_DIR / "survey_long_analysis_responses.csv", index=False)
response_frequency.to_csv(OUTPUT_DIR / "response_frequency_initial.csv", index=False)
question_diagnostics.to_csv(OUTPUT_DIR / "question_diagnostics.csv", index=False)

print("Saved exploration outputs to:")
print(OUTPUT_DIR)
