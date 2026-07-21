# Validation Guide for Non-Coders

This guide helps you check whether the Python scripts produced correct results **without reading any code**. All checks are done by opening Excel/CSV files and comparing numbers.

---

## 1. Quick file map

| Folder | What it contains | File to open first |
|---|---|---|
| `outputs/exploration/` | First look at the data: how many sheets, rows, missing values | `workbook_overview.csv` |
| `outputs/cleaned/` | Cleaned answers + frequency tables | `question_frequency_cleaned.csv` |
| `outputs/multi_response/` | Multi-answer questions broken into indicators | `multi_response_summary.csv` |
| `outputs/descriptive_results/` | Final thesis-ready tables by theme | `descriptive_results_workbook.xlsx` |
| `outputs/validation/` | List of problems to review | `validation_action_list.csv` |
| `outputs/synopsis_mapping/` | Which question answers which objective/hypothesis | `objectives_with_top_findings.xlsx` |

---

## 2. Five simple checks to validate the results

### Check 1: Did all respondents get counted?

Open `outputs/exploration/workbook_overview.csv`.

You should see:

| sheet | respondent_columns |
|---|---|
| General Public | 52 |
| Govt Officials | 11 |
| Mahila Mukhiya | 8 |
| Traditional Leader | 5 |
| Women Representative | 8 |

If these numbers do not match your original `Surveys.xlsx`, something went wrong.

---

### Check 2: Are the denominators sensible?

In any final table, `denominator_n` is the number of people who answered that question.

- For **General Public**, most denominators should be close to **52**.
- For **Govt Officials**, close to **11**.
- For **Mahila Mukhiya**, close to **8**.
- For **Traditional Leader**, close to **5**.
- For **Women Representative**, close to **8**.

If you see a denominator like **56** for a Women Representative question, it is probably a **matrix question** that was not split correctly. The pipeline now automatically restructures Q19, Q21, Q23 into sub-items like 19.1, 19.2, etc.

---

### Check 3: Spot-check a few answers by hand

Pick one simple question, for example:

> General Public Q2: Gender

Open `outputs/descriptive_results/02_general_public_awareness_access_tables.csv` and look for Q2. You should see something like:

| answer | count | percent_of_respondents |
|---|---|---|
| Male | 49 | 94.23 |
| Female/Woman | 3 | 5.77 |

Now go back to `Surveys.xlsx` → `General Public` sheet and manually count the Male/Female entries in row 2. They should match.

Do this for 2-3 questions. If the counts match, the reshaping and cleaning are working correctly.

---

### Check 4: Review the cleaning impact

Open `outputs/cleaned/question_cleaning_impact.csv`.

This shows, for each question:
- `raw_unique_responses`: how many different wordings existed before cleaning
- `cleaned_unique_responses`: how many remain after cleaning
- `changed_rows`: how many answers were modified

A large `unique_reduction` is usually good (e.g., "18-25", "18–25", "18 25" became one category). But if you see a question where many answers were changed and you do not agree with the grouping, note it down.

Also open `outputs/cleaned/cleaning_summary.csv` to see how many answers were put into each category.

---

### Check 5: Read the validation action list

Open `outputs/validation/validation_action_list.csv`.

This is your **to-do list**. The `severity` column tells you how important each issue is:

- **high**: must fix before writing results
- **medium**: important, decide how to handle
- **low**: minor, fix if time permits

The main issues right now are:

1. **Count logic errors (high)** — matrix questions in Women Representative Q19, Q21, Q23 are now automatically restructured by the pipeline.
2. **High fragmentation (medium)** — open-ended questions with too many unique answers. These need thematic grouping.
3. **Missing-dominant questions (medium)** — mostly agriculture questions in General Public where many people said "Not mentioned". Decide how to report them.
4. **Theme review (low)** — some questions are under the wrong theme heading. Easy to fix.

---

## 3. What "Not mentioned/Do not know" means

When a respondent left a cell blank or wrote "don't know", the code labels it as **"Not mentioned/Do not know"**. This is **not an error**. It is a valid response category that tells you:

- Some people did not know the answer.
- Some questions were not applicable (e.g., non-landowners asked about land).
- Some people chose not to answer.

In your thesis, report these as **missing/non-response** or **do not know**, depending on the question.

---

## 4. How to answer the synopsis questions (without coding)

### Step A: Know your four objectives and hypotheses

From the synopsis:

| Objective | Hypothesis |
|---|---|
| Obj 1: Impact of 73rd Amendment on representation & participation | H1: Reservation increased women's representation/participation → empowerment |
| Obj 2: Effectiveness of capacity building initiatives | H2: Capacity building enhances participation & empowerment |
| Obj 3: Role of ICT in promoting participation | H3: ICT played a crucial role |
| Obj 4: Participation → empowerment & community development | H4: Participation contributed to empowerment & community development |

### Step B: Use the mapping file

Open `outputs/synopsis_mapping/objectives_with_top_findings.xlsx`.

This file lists every survey question that relates to each objective, plus the most common answer (`top_answer`) and percentage (`top_percent`).

For example, for **Obj 4**, you can see that:
- General Public Q12: 76.92% said women can be good/equal leaders.
- General Public Q14: 46.15% said there were improvements under a woman Mukhiya.
- Women Representative Q23: most said their confidence/mobility/decision-making/respect increased.

Use these top-line numbers as evidence in your results chapter.

### Step C: Group findings by theme

Open `outputs/descriptive_results/descriptive_results_workbook.xlsx`.

It has sheets like:
- `01_respondent_profile_tables.csv`
- `06_ict_digital_access_tables.csv`
- `07_agriculture_livelihood_tables.csv`

Write one section of your thesis per theme, using the tables directly.

### Step D: Handle open-ended questions

For questions where people wrote sentences (not tick-box answers), the current output just lists each sentence and how many times it appeared. You need to **read them and group into themes**.

Example for **Mahila Mukhiya Q26** ("Work you are most proud of"):
- Read all 8 answers.
- Group them into 3-4 themes, e.g., "Sanitation/toilets", "Roads/infrastructure", "Welfare schemes".
- Report: "Out of 8 Mahila Mukhiya respondents, X mentioned sanitation, Y mentioned roads..."

### Step E: Interpret, do not just report

For each objective, write:

1. **Finding**: What the data shows (percentage, mean, theme).
2. **Interpretation**: What it means for women empowerment.
3. **Link to hypothesis**: Does it support or contradict the hypothesis?

Example:

> Finding: 75% of Women Representatives own a smartphone, but 75% also reported receiving no training on ICT for government work (Q33).  
> Interpretation: Access to technology exists, but capacity to use it effectively is lacking.  
> Link to H2/H3: This partially supports H3 (ICT access) but weakens H2 (capacity building is insufficient).

---

## 5. Recommended order of work

1. ✅ **Validate the easy counts** (Check 1–3 above).
2. ✅ **Matrix questions are fixed automatically** by the pipeline (Q19, Q21, Q23 are split into sub-items like 19.1, 19.2, etc.).
3. 📝 **Thematic coding of key open-ended questions** for Mahila Mukhiya, Govt Officials, Traditional Leader.
4. 🎯 **Re-check theme assignments** using `validation/theme_mismatch_review.csv`.
5. 📊 **Create charts** from the final tables.
6. 📖 **Write results chapter** using `objectives_with_top_findings.xlsx`.

---

## 6. When to ask for help

Ask for help when:
- A denominator looks impossible (e.g., larger than the number of respondents and it is not a multi-response question).
- A percentage is above 100 in a single-response table.
- You disagree with how an answer was coded/grouped.
- You need new charts or cross-tabs.

---

## 7. One-page cheat sheet

| If you want to... | Open this file |
|---|---|
| See all final numbers | `outputs/descriptive_results/descriptive_results_workbook.xlsx` |
| Know which question answers which objective | `outputs/synopsis_mapping/objectives_with_top_findings.xlsx` |
| Check for problems | `outputs/validation/validation_action_list.csv` |
| See what the code changed | `outputs/cleaned/cleaning_summary.csv` |
| Read raw open-ended answers | `outputs/cleaned/cleaned_analysis_responses.csv` |
| Understand matrix issue | `outputs/validation/likely_matrix_questions.csv` |
