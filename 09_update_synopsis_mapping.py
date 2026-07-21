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

# Expand matrix parent questions into their corrected sub-items
matrix_expansions = {
    ("Women Representative", "19"): ["19.1", "19.2", "19.3", "19.4"],
    ("Women Representative", "21"): ["21.1", "21.2", "21.3", "21.4", "21.5", "21.6", "21.7"],
    ("Women Representative", "23"): ["23.1", "23.2", "23.3", "23.4"],
}
expanded_rows = []
for _, row in mapping_df.iterrows():
    key = (row["respondent_group"], row["question_no"])
    if key in matrix_expansions:
        for sub in matrix_expansions[key]:
            expanded_rows.append({
                "respondent_group": row["respondent_group"],
                "question_no": sub,
                "objective": row["objective"],
                "hypothesis": row["hypothesis"],
            })
    else:
        expanded_rows.append(row.to_dict())
mapping_df = pd.DataFrame(expanded_rows)

q_summary["question_no_str"] = q_summary["question_no"].apply(
    lambda x: str(int(x)) if pd.notna(x) and x == int(x) else str(x)
)
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
