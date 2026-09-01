# %%
# Step 9: Update synopsis mapping and top findings
# This script regenerates the objectives_with_top_findings.xlsx workbook and
# the TOP_FINDINGS_BY_OBJECTIVE.md markdown summary, preferring thematic
# coding results where available.

from pathlib import Path
import sys

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = PROJECT_DIR / "outputs"
MAPPING_DIR = OUTPUTS_DIR / "synopsis_mapping"
MAPPING_DIR.mkdir(parents=True, exist_ok=True)

Q_SUMMARY_PATH = OUTPUTS_DIR / "descriptive_results" / "question_level_summary.csv"
MAPPING_FILE = MAPPING_DIR / "objectives_with_top_findings.xlsx"
MD_FILE = MAPPING_DIR / "TOP_FINDINGS_BY_OBJECTIVE.md"


# %%
# Step 1: Load question summary and prefer thematic rows

q_summary = pd.read_csv(Q_SUMMARY_PATH)

# For each (respondent_group, question_no), keep thematic row if it exists,
# otherwise keep the ordinary (single/multi/raw) row.
q_summary = q_summary.sort_values(
    "result_type",
    key=lambda col: col.eq("thematic").astype(int),
    ascending=False,
)
q_summary = q_summary.drop_duplicates(
    subset=["respondent_group", "question_no"],
    keep="first",
)


# %%
# Step 2: Load mapping of questions to synopsis objectives/hypotheses
# The mapping is stored in config/question_hypothesis_mapping.csv so it can be
# edited directly (Excel/Notepad) or through the Streamlit app.

CONFIG_DIR = PROJECT_DIR / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
MAPPING_CSV = CONFIG_DIR / "question_hypothesis_mapping.csv"

if MAPPING_CSV.exists():
    mapping_df = pd.read_csv(MAPPING_CSV)
    mapping_df["question_no"] = mapping_df["question_no"].astype(str)
else:
    # Fallback default mapping if the CSV is missing
    default_mapping = [
        # Obj 1
        ("Women Representative", "2", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "14", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "15", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "16", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "17", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "18", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "19", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Women Representative", "20", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Mahila Mukhiya", "2", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Mahila Mukhiya", "15", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Mahila Mukhiya", "17", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Govt Officials", "15", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Govt Officials", "20", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Traditional Leader", "15", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Traditional Leader", "16", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        ("Traditional Leader", "20", "Obj 1: 73rd Amendment impact on representation & participation", "H1: 73rd Amendment increased representation/participation → empowerment"),
        # Obj 2
        ("Women Representative", "21", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Women Representative", "22", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Women Representative", "33", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Govt Officials", "16", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Govt Officials", "24", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Govt Officials", "25", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Govt Officials", "26", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        ("Mahila Mukhiya", "24", "Obj 2: Effectiveness of capacity building initiatives", "H2: Capacity building enhances participation & empowerment"),
        # Obj 3
        ("General Public", "9", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("General Public", "10", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("General Public", "11", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("General Public", "15", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "29", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "30", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "31", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "32", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "33", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Women Representative", "34", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Govt Officials", "21", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Govt Officials", "22", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Govt Officials", "23", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Mahila Mukhiya", "21", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Mahila Mukhiya", "22", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Mahila Mukhiya", "23", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        ("Traditional Leader", "22", "Obj 3: Role of ICT in promoting participation", "H3: ICT played a crucial role"),
        # Obj 4
        ("Women Representative", "19", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Women Representative", "23", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Women Representative", "24", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("General Public", "12", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("General Public", "13", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("General Public", "14", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("General Public", "18", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("General Public", "19", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Mahila Mukhiya", "16", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Mahila Mukhiya", "25", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Mahila Mukhiya", "26", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
        ("Mahila Mukhiya", "27", "Obj 4: Participation → empowerment & community development", "H4: Participation contributed to empowerment & community development"),
    ]
    mapping_df = pd.DataFrame(
        default_mapping,
        columns=["respondent_group", "question_no", "objective", "hypothesis"],
    )
    mapping_df["question_no"] = mapping_df["question_no"].astype(str)
    MAPPING_CSV.parent.mkdir(parents=True, exist_ok=True)
    mapping_df.to_csv(MAPPING_CSV, index=False)

# NOTE: matrix sub-items no longer need expanding. In the current workbook each
# sub-item already has its own Question No (involvement = Q19-Q22,
# challenges = Q24-Q31, change-since = Q33-Q36), so they are mapped directly in
# config/question_hypothesis_mapping.csv like any other question.

def as_question_key(value):
    """Normalize a question number to a comparable string ('19', '19a')."""
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


q_summary["question_no_str"] = q_summary["question_no"].map(as_question_key)
mapping_df["question_no"] = mapping_df["question_no"].map(as_question_key)

# Warn about mapping entries that no longer match any question in the data.
available = set(zip(q_summary["respondent_group"], q_summary["question_no_str"]))
unmatched = [
    f"{g} Q{q}"
    for g, q in zip(mapping_df["respondent_group"], mapping_df["question_no"])
    if (g, q) not in available
]
if unmatched:
    print(f"WARNING: {len(set(unmatched))} mapped questions have no results:")
    for item in sorted(set(unmatched)):
        print(f"  - {item}")
    print("  (Question numbers may have shifted; update config/question_hypothesis_mapping.csv)")
# Drop the original numeric question_no from q_summary to avoid column name collisions
q_summary = q_summary.drop(columns=["question_no"])
merged = mapping_df.merge(
    q_summary,
    left_on=["respondent_group", "question_no"],
    right_on=["respondent_group", "question_no_str"],
    how="left",
)

merged["finding_type"] = merged["result_type"].apply(
    lambda x: "Thematic coding" if x == "thematic" else "Mapped question"
)

final_cols = [
    "objective",
    "hypothesis",
    "respondent_group",
    "question_no",
    "question",
    "finding_type",
    "top_answer",
    "top_count",
    "denominator_n",
    "top_percent",
]
for col in final_cols:
    if col not in merged.columns:
        merged[col] = ""

merged = merged[final_cols]
merged.to_excel(MAPPING_FILE, index=False)
print(f"Saved synopsis mapping: {MAPPING_FILE}")


# %%
# Step 3: Write TOP_FINDINGS_BY_OBJECTIVE.md

md_lines = [
    "# Top Findings by Synopsis Objective",
    "",
    "This file gives the most important number/answer for each question linked to a synopsis objective.",
    "Use it while writing the Results chapter.",
    "",
]

for objective, group_df in merged.groupby("objective", sort=False):
    md_lines.append(f"## {objective}")
    md_lines.append("")
    for _, row in group_df.iterrows():
        group = row["respondent_group"]
        qno = row["question_no"]
        question = str(row["question"]).replace("\n", " ").strip()
        top = row["top_answer"]
        count = row["top_count"]
        denom = row["denominator_n"]
        pct = row["top_percent"]
        ftype = row["finding_type"]
        if pd.isna(top) or str(top).strip() == "":
            continue
        md_lines.append(
            f"- **{group} Q{qno}**: {top} ({count}/{denom}, {pct}%) — {question} "
            f"_[{ftype}]_"
        )
    md_lines.append("")

MD_FILE.write_text("\n".join(md_lines), encoding="utf-8")
print(f"Saved top findings markdown: {MD_FILE}")
