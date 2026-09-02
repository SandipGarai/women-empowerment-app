# Data update notes — September 2026 workbook (revision 2)

Status: **all validation checks PASS.** 552 result rows, 0 unmatched mapping entries.

---

## What you fixed in the Excel

| | |
|---|---|
| Traditional Leader `19 a` / `19b` | Renumbered to Q20 / Q21; everything from old Q20 onward shifted **+2**. Blank spacer row removed. `Question No` is now a clean integer column. |
| WR2's invalid "Yes" on Q21 | Cleared. That battery no longer has an out-of-range value. |

Both fixes are confirmed in the data and reflected throughout the results.

---

## Three coding bugs found and fixed this round

### 1. The flagged one: General Public Q13 "Biggest difficulty?"

One respondent answered **"No difficulty"**, which matched none of the coding
rules and was silently dropped — counts came to 52 against a denominator of 53.
Fixed by testing for "no difficulty" / "no problem" first.

### 2. The serious one: the same question was miscoded

While fixing the above I found a much bigger problem in the same rules.

The most common answer, **"Lack of Support from Men" (28 of 53 respondents)**, was
being matched by the pattern `support` in the *family/husband* rule, and was **not**
matched by the men/patriarchy rule (whose patterns were `village men`, `patriarch`,
`male` — none of which match a bare "Men"). The results therefore said:

| | Before | After |
|---|---|---|
| Family/husband permission or support | **31 (58.5%)** ← reported as top finding | 3 (5.7%) |
| Men do not listen / patriarchy | 0 (0.0%) | **28 (52.8%)** ← correct top finding |
| Total coded | 52 of 53 | 53 of 53 |

This was a wrong finding, not just a wrong count. If you have already drafted
anything about public perceptions of women leaders' difficulties, **recheck it**:
the barrier the public identifies is lack of support from men, not family
permission. Fixed by adding `\bmen\b` to the patriarchy rule and removing the
over-broad bare `support` from the family rule.

### 3. "Names of Crops" was being deleted as a personal identifier

`02_clean_and_code_surveys.py` excluded any question whose text *contained* the
substring `name`. That correctly caught "Name (Optional)" — and also caught
**"Names of Crops Sown in Kharif Season"** and **"...Rabi Season"** for both Women
Representatives (Q50, Q51) and Traditional Leaders (Q36, Q37). Four questions of
agricultural data were being discarded before analysis began.

Name fields are now matched with an anchored pattern (`^name`), so only genuine
identifier fields are excluded.

### Structural safeguard

Multi-response questions now emit an explicit **"Uncoded - needs manual review"**
category when a response matches no rule, instead of dropping it. A silently
missing response can no longer hide as a vague validation warning.

---

## General Public Q5 — the question I asked you about

**What I meant, plainly:** `02_clean_and_code_surveys.py` keeps a list of
"identifier" questions to exclude from analysis — things like Name, Village,
Block, District, which describe *who* the respondent is rather than *what they
think*. The phrase `who the mukhiya` was on that list, so **"Do you know who the
Mukhiya is?" was being thrown away as if it were a name field.**

It is not a name field. It is a real Yes/No awareness question, and it is evidence
for Objective 1. I did not change it last time because deciding which questions
count as data is a research decision, not a bug fix — I did not want to alter your
methodology without asking.

**I have now included it**, since it is clearly substantive. The finding:
**53 of 53 (100%) of the general public know who their Mukhiya is.**

To reverse this, add `r"^do you know who the mukhiya"` back to
`profile_name_patterns` in `02_clean_and_code_surveys.py` and re-run.

---

## The mapping: `config/question_hypothesis_mapping.csv`

This is the file that answers your synopsis questions. It links each survey
question to an objective and a hypothesis.

**It is now generated, not hand-written.** Run:

```
python config/build_question_mapping.py
```

### Why

A CSV of raw question numbers rots every time the workbook is renumbered. Your
Traditional Leader sheet just shifted by +2 from Q20 onward — a hand-written
mapping would have quietly pointed a dozen ICT questions at the wrong objective
with no error message.

`config/build_question_mapping.py` declares the mapping against a distinctive
**phrase** from each question and looks the number up from the current data. If a
phrase stops matching, or matches two questions, it **stops with an error naming
the problem** instead of writing a wrong file. All 96 phrases currently resolve to
exactly one question each.

To change which evidence supports which objective, edit `MAPPING_SPEC` in that
script and re-run it. Do not hand-edit the CSV — it will be overwritten.

### Current coverage (112 rows, 0 unmatched)

| Objective | Questions | Respondent groups |
|---|---|---|
| Obj 1 — 73rd Amendment → representation/participation | 22 | 5 |
| Obj 2 — Capacity building | 7 | 3 |
| Obj 3 — Role of ICT | 23 | 5 |
| Obj 4 — Participation → empowerment/development | 26 | 5 |

Deliberately **not** mapped: name, age, education, caste, occupation, landholding
and the agriculture block. Those describe your sample and belong in the synopsis
chapter "Socio Economic profile of the respondents", not to any objective.

### Objective 2 is still your weak point

Seven questions across three groups (WR Q27, Q46; Govt Officials Q16, Q17, Q19,
Q24, Q25; Mahila Mukhiya Q24) — and several are shared with Objective 3 rather
than being dedicated capacity-building measures. Note also **WR Q27, "Lack of
knowledge about rules and procedures", has the lowest mean of the challenge
battery among the non-transport items (3.00), with 50% rating it 1–2.** Your
representatives do not report a training deficit as a major barrier. That is a
finding, but it means H2 is supported thinly and mostly by officials' opinions
rather than by representatives' own experience. Consider stating H2 more modestly
in the thesis, or framing Objective 2 as exploratory.

---

## Two judgement calls the code makes for you

`07_thematic_coding.py` prints these on every run. Check them:

```
AMBIGUOUS: Govt Officials 'training' matched Q16, Q24, Q25 -> using Q16
AMBIGUOUS: Women Representative 'biggest challenge' matched Q32, Q47 -> using Q32
```

Both are currently correct — WR Q47 is about ICT challenges specifically, not the
general "biggest challenge" — but they are the script choosing on your behalf, so
they are worth a glance each time.

---

## Remaining data gaps (not errors — genuine non-response)

Only 8 Women Representatives were surveyed, so each blank is a large proportional
loss:

| Question | Answered |
|---|---|
| Q20 Discussing the budget | 5 / 8 |
| Q21 Monitoring schemes | 5 / 8 |
| Q22 Solving disputes | 5 / 8 |
| Q23 Opinion heard by male colleagues | 6 / 8 |

Note that Q19 (planning, 8/8, mean 4.25) has full response while budget and
monitoring do not. If the blanks mean "not involved" rather than "not asked", the
means for Q20–Q22 are optimistic. Worth confirming from your field notes and
stating explicitly in the methodology chapter.

---

## Where to write from

- `outputs/synopsis_mapping/TOP_FINDINGS_BY_OBJECTIVE.md` — headline result per question, grouped by objective
- `outputs/synopsis_mapping/objectives_with_top_findings.xlsx` — same, as a spreadsheet
- `outputs/matrix_corrected/matrix_scale_statistics.csv` — means and SDs for the 1–5 batteries
- `outputs/descriptive_results/descriptive_results_workbook.xlsx` — every frequency table
- `outputs/thematic_coding/review/thematic_coding_review.xlsx` — the 13 open-ended responses awaiting your manual review

### Interpretation caution

With 8 Women Representatives, 8 Mahila Mukhiya, 11 Govt Officials and 5
Traditional Leaders, these are **descriptive patterns, not significance tests**.
One respondent shifts a Women Representative percentage by 12.5 points. Report
counts alongside percentages (the outputs already do), and avoid language implying
statistical inference. The General Public group (n=53) is the only one where
percentages are reasonably stable on their own.

---

## Why the app appeared to ignore your upload

Uploading a file only replaced `Surveys.xlsx` on disk. Every results tab is built
from the CSVs in `outputs/`, which are written by the analysis scripts — so until
you clicked **Run Full Pipeline**, you kept seeing the previous run's numbers with
nothing on screen indicating they were out of date. (The Data Preview tab reads the
workbook directly, which is why *that* tab did show your new data.)

A second problem compounded it: the six data loaders were declared as
`@st.cache_data` with **no arguments**, so their cache key was just the function
name. Streamlit therefore kept serving the first results it ever read, even after
the pipeline rewrote the files on disk.

Three fixes:

1. **Uploading now triggers the analysis automatically.** A new upload is detected
   by content hash, the cache is dropped, and the pipeline runs. There is a
   checkbox in the sidebar to turn this off if you prefer the manual button.
2. **Loaders are cached on file modification time and size**, so any change on
   disk invalidates the cache. Verified: rewriting a results CSV is picked up on
   the next read without any explicit cache clear.
3. **A red banner appears across the top of every tab** when the results in
   `outputs/` were produced from a different file than the one currently uploaded.
   The app records the hash of the analysed workbook in `outputs/.pipeline_stamp.json`
   and compares on every page load.

Tested end to end: analysed the workbook, changed 10 answers on General Public Q13,
and the app reported `stale` before re-running and the corrected counts
(men/patriarchy 28 → 18, household work 10 → 20) after.

### One thing to know about Streamlit Cloud

`Surveys.xlsx` and `outputs/` are both in `.gitignore`, so they are not in your
repo. Streamlit Cloud's filesystem is also **ephemeral** — it is wiped whenever the
app reboots or redeploys. After a restart you will need to upload the workbook
again and let it re-analyse. That is expected behaviour, not a fault; keeping
survey data out of a public repo is the right call.


---

# Revision 3 — validation, coding and manuscript

All 12 validation checks now PASS.

## "Expected 53, found 269"

Reproduced exactly: a single stray character far to the right of the General Public
sheet makes pandas read 215 phantom `Unnamed:` columns and count them as
respondents. Scripts 01 and 02 now ignore columns with no header and no data.
Verified against a deliberately corrupted copy of your file: it now reports 53.

The hard-coded `expected_counts` dictionary was also replaced. It now checks
whether every respondent in the workbook survives into the analysed data, which is
a real integrity question, instead of comparing against a fixed number that goes
stale whenever the sample changes.

## "51 fragmented questions"

Mostly noise. Age, landholding, crop lists and 1-5 scale items are supposed to have
many distinct values. The check now classifies each case by reason and flags only
genuine ones: 51 → 8. Thematic coding rules were written for all 8, so the check
now passes.

## "Uncoded: needs manual review"

That label is the safety net reporting that a response matched no coding rule.
It is now zero. When it reappears, fix it in one of two places:

- `03_multi_response_coding.py` — for list-type answers (crops, livestock,
  information sources, difficulties). Add the missing keyword to the relevant
  `crop_patterns` or rule list.
- `07_thematic_coding.py` — for open-ended opinion questions. Add a theme and its
  patterns to `THEMATIC_RULES`.

The uncoded responses themselves are listed in
`outputs/multi_response/multi_response_long.csv` (filter `indicator == "uncoded_response"`)
and `outputs/thematic_coding/review/`.

## Two more bugs found this round

**Script 07 excluded any question containing "panchayat".** The profile filter used
substring matching, so 22 substantive questions were locked out of thematic coding
entirely, including most of the Traditional Leader ICT block. Now anchored.

**Case variants were splitting categories.** "Yes"/"yes" and
"Cooperative"/"cooperative" produced separate rows in frequency tables — Women
Representative Q37 reported "Yes 5/8" and "yes 3/8" instead of the correct
**Yes 8/8**. Short categorical answers are now capitalisation-harmonised, and a
small explicit list of unambiguous typo corrections was added ("Ward Memebr" →
"Ward Member", which was splitting the position-held table).

## Editing the mapping: two routes that overwrite each other

1. **In the app.** Question Mapping tab → edit the Objective and Hypothesis
   dropdowns → Save. Writes to `config/question_hypothesis_mapping.csv` and
   survives pipeline re-runs.
2. **`config/build_question_mapping.py`.** Regenerates the whole CSV from question
   text, so it stays correct when questions are renumbered.

Running the builder **discards** edits made in the app. For a permanent change, add
it to `MAPPING_SPEC` inside the builder script. A notice explaining this now appears
in the app.

"Thematic coding" in the mapping table means that row's finding came from grouping
free-text answers into themes by keyword rules, rather than from a plain frequency
count. Open-ended questions can show both row types.

## An error I made in the manuscript, and corrected

My first draft argued that women representatives are admitted to consultative
business but excluded at a "fiscal threshold" — high involvement in planning, low in
budgeting. **The data do not support this.** Monitoring of scheme implementation is
the highest-rated activity (mean 4.80), not the lowest, and all four activity means
fall between 4.0 and 4.8 — a spread well inside what one respondent can move with
n = 5 to 8.

The manuscript was rewritten around what the data actually show: representatives'
self-assessment is uniformly favourable, and it is **not corroborated by citizens**.
That divergence — 98% would approach the Mukhiya, 45% of those who did were helped —
is the real finding, and it is a stronger one, because it does not depend on any
fragile ordering of four means.

If you take one thing from this: with n = 8, do not build an argument on the rank
order of close means. Build it on the places where two independent sources disagree.
