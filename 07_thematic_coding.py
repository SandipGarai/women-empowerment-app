# %%
# Step 1: Imports and paths
# This script performs thematic coding on important open-ended questions.
# It uses keyword-based rules to assign themes, then produces frequency tables.
# The rules are conservative: uncertain answers are left for manual review.

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
OUTPUT_DIR = PROJECT_DIR / "outputs" / "thematic_coding"
REVIEW_DIR = OUTPUT_DIR / "review"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_ANALYSIS_PATH = CLEANED_DIR / "cleaned_analysis_responses.csv"


# %%
# Step 2: Helper functions

def normalize(text):
    """Normalize text for matching."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contains_any(text, patterns):
    """Check if any regex pattern appears in text."""
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def starts_with_any(text, patterns):
    """Check if text starts with any of the patterns."""
    for pattern in patterns:
        if re.match(pattern, text):
            return True
    return False


def safe_sheet_name(name):
    """Make an Excel sheet name safe (<=31 chars, no forbidden chars)."""
    name = re.sub(r"[:\\/\?\*\[\]]", "_", str(name))
    name = name.strip("'")
    if len(name) > 31:
        name = name[:31]
    return name


# %%
# Step 3: Define thematic coding rules for key open-ended questions
# Each entry: (respondent_group, question_no, question_contains, theme_rules)
# theme_rules is a list of (theme_label, [regex patterns])
# Patterns support two special helpers handled separately:
#   - "__STARTS_WITH_YES__": if response begins with "yes" (after normalizing)
#   - "__STARTS_WITH_NO__": if response begins with "no"

THEMATIC_RULES = [
    # ----------------- Mahila Mukhiya -----------------
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 26,
        "question_contains": "most proud",
        "themes": [
            ("Welfare schemes/poverty relief", [r"needy", r"poor", r"food", r"clothing", r"ration", r"pension", r"benefit"]),
            ("Sanitation/toilets", [r"toilet", r"sanitation", r"bathroom", r"latrine", r"open defecation", r"odf"]),
            ("Roads/transport", [r"road", r"drainage", r"street", r"path"]),
            ("Water/irrigation", [r"water", r"well", r"handpump", r"irrigation", r"pond", r"tap"]),
            ("Education/school", [r"school", r"education", r"student", r"teacher"]),
            ("Housing/construction", [r"house", r"housing", r"home", r"construction", r"building"]),
            ("General village development", [r"village development", r"development work", r"panchayat"]),
            ("Electricity", [r"electric", r"solar", r"light"]),
            ("Community empowerment", [r"empower", r"women", r"confidence", r"awareness"]),
        ],
    },
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 27,
        "question_contains": "could not",
        "themes": [
            ("Infrastructure/roads", [r"road", r"drainage", r"community hall", r"building"]),
            ("Water/irrigation", [r"water", r"well", r"irrigation", r"pond"]),
            ("Education/facilities for children", [r"school", r"children", r"facility"]),
            ("Funds/budget", [r"fund", r"money", r"budget", r"financial", r"lack of money"]),
            ("Official delays", [r"official", r"delay", r"bdo", r"department", r"paper"]),
            ("Land issues", [r"land", r"plot", r"possession"]),
            ("Family/community opposition", [r"family", r"husband", r"oppose", r"community", r"resistance"]),
            ("Time/workload constraints", [r"lack of time", r"no time", r"monitoring", r"completion"]),
        ],
    },
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 15,
        "question_contains": "how you became",
        "themes": [
            ("Reservation", [r"reservation", r"reserved", r"seat"]),
            ("Family support", [r"family", r"husband", r"father", r"mother", r"support", r"happy"]),
            ("Community request", [r"community", r"village", r"people", r"request", r"asked"]),
            ("Self-motivation", [r"self", r"myself", r"motivat", r"interest"]),
            ("Political party", [r"party", r"ticket", r"political"]),
            ("Social service", [r"service", r"help", r"work", r"social"]),
            ("Election process", [r"election", r"contest", r"contested"]),
        ],
    },
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 16,
        "question_contains": "important decision",
        "themes": [
            ("Roads/drainage", [r"road", r"drainage"]),
            ("Sanitation/toilets", [r"toilet", r"sanitation"]),
            ("Water/irrigation", [r"water", r"well", r"irrigation"]),
            ("Education/school", [r"school", r"education"]),
            ("Social regulation (alcohol/gambling)", [r"alcohol", r"liquor", r"gambling", r"addiction"]),
            ("Welfare schemes", [r"scheme", r"pension", r"ration"]),
            ("Got support", [r"support", r"helped", r"cooperat", r"accepted", r"convinced"]),
            ("Faced opposition", [r"oppose", r"resistance", r"problem", r"difficult"]),
        ],
    },
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 25,
        "question_contains": "special challenges",
        "themes": [
            ("Education/awareness", [r"education", r"awareness", r"literacy", r"knowledge"]),
            ("Patriarchy/male dominance", [r"patriarch", r"male", r"men", r"dominance", r"society"]),
            ("Family/husband opposition", [r"husband", r"family", r"home", r"permission"]),
            ("Social discrimination", [r"discrimination", r"caste", r"tribe", r"tribal"]),
            ("Economic/poverty", [r"poor", r"poverty", r"economic", r"money", r"financial"]),
            ("Transport/mobility", [r"transport", r"travel", r"mobility", r"vehicle"]),
            ("Dual burden", [r"housework", r"household", r"dual", r"family responsibility"]),
        ],
    },
    {
        "respondent_group": "Mahila Mukhiya",
        "question_no": 28,
        "question_contains": "advice",
        "themes": [
            ("Education", [r"education", r"study", r"literate"]),
            ("Confidence/courage", [r"confidence", r"courage", r"fear", r"brave"]),
            ("Social service", [r"service", r"help", r"social", r"people"]),
            ("Awareness/schemes", [r"awareness", r"knowledge", r"learn", r"scheme", r"government"]),
            ("Employment/independence", [r"job", r"employment", r"work", r"independent"]),
        ],
    },
    # ----------------- Govt Officials -----------------
    {
        "respondent_group": "Govt Officials",
        "question_no": 17,
        "question_contains": "administrative hurdles",
        "themes": [
            ("Literacy/education", [r"literacy", r"education", r"read", r"write", r"qualification"]),
            ("Economic status", [r"economic", r"financial", r"poor", r"poverty", r"money"]),
            ("Patriarchy/social attitude", [r"patriarch", r"male", r"society", r"attitude", r"mindset", r"domain"]),
            ("Proxy influence", [r"proxy", r"husband", r"family member"]),
            ("Lack of training", [r"training", r"capacity", r"knowledge", r"awareness"]),
            ("Dual burden", [r"housework", r"household", r"family responsibility"]),
            ("Transport", [r"transport", r"travel", r"mobility"]),
            ("No major hurdles", [r"no", r"easy", r"nothing"]),
        ],
    },
    {
        "respondent_group": "Govt Officials",
        "question_no": 20,
        "question_contains": "proxy rule",
        "themes": [
            ("Successful", [r"__STARTS_WITH_YES__", r"empowered", r"empower", r"become", r"good"]),
            ("Proxy rule", [r"proxy", r"husband", r"family", r"not independent", r"not freely"]),
            ("Mixed/both", [r"both", r"mixed", r"some", r"partial", r"but"]),
            ("Limited impact", [r"limited", r"not much", r"nominal", r"only representation"]),
        ],
    },
    {
        "respondent_group": "Govt Officials",
        "question_no": 15,
        "question_contains": "differences",
        "themes": [
            ("Women more committed", [r"commit", r"dedicat", r"sincere", r"serious"]),
            ("Women less confident", [r"confidence", r"hesitant", r"shy", r"nervous"]),
            ("Men more dominant", [r"male", r"men", r"dominant", r"patriarch"]),
            ("No major difference", [r"^no$", r"no major", r"no significant", r"no difference", r"not much difference", r"same", r"equal", r"depends on both"]),
            ("Women need more support", [r"support", r"training", r"guidance"]),
        ],
    },
    {
        "respondent_group": "Govt Officials",
        "question_no": 16,
        "question_contains": "training",
        "themes": [
            ("Need regular training", [r"training", r"capacity", r"regular", r"necessary", r"required", r"__STARTS_WITH_YES__"]),
            ("Need technical/digital training", [r"technical", r"computer", r"digital", r"ict"]),
            ("Need leadership/admin training", [r"leadership", r"administrative", r"panchayat", r"rule"]),
            ("Awareness/education gaps", [r"education", r"awareness", r"literacy", r"understanding"]),
            ("Confidence/perception gaps", [r"confidence", r"perception", r"capable", r"limited"]),
            ("Financial/resource support", [r"fund", r"money", r"financial", r"resource"]),
        ],
    },
    # ----------------- Women Representative -----------------
    {
        "respondent_group": "Women Representative",
        "question_no": 22,
        "question_contains": "biggest challenge",
        "themes": [
            ("Confidence/acceptance", [r"confidence", r"people", r"accept", r"trust", r"belief"]),
            ("Male/patriarchal opposition", [r"male", r"men", r"patriarch", r"society", r"oppose"]),
            ("Family/husband opposition", [r"husband", r"family", r"home", r"permission"]),
            ("Transport", [r"transport", r"travel", r"vehicle", r"road"]),
            ("Rules/procedures knowledge", [r"rule", r"procedure", r"knowledge", r"paper", r"document"]),
            ("Dual burden", [r"housework", r"household", r"family responsibility", r"time"]),
            ("Official non-cooperation", [r"official", r"cooperat", r"bdo", r"department"]),
            ("No major challenge", [r"__STARTS_WITH_NO__", r"nothing", r"none"]),
        ],
    },
    {
        "respondent_group": "Women Representative",
        "question_no": 15,
        "question_contains": "motivated",
        "themes": [
            ("Community request", [r"community", r"village", r"people", r"request"]),
            ("Family encouragement", [r"family", r"husband", r"encourag", r"support"]),
            ("Self-motivation", [r"self", r"myself", r"motivat", r"interest"]),
            ("Political party", [r"party", r"ticket", r"political"]),
            ("Reservation", [r"reservation", r"reserved", r"seat"]),
            ("Social service", [r"service", r"help", r"social", r"work"]),
        ],
    },
    # ----------------- General Public -----------------
    {
        "respondent_group": "General Public",
        "question_no": 13,
        "question_contains": "difficulty",
        "themes": [
            ("Male non-acceptance", [r"men", r"male", r"don t listen", r"not listen", r"not accept"]),
            ("Housework/dual burden", [r"housework", r"household", r"domestic", r"family work", r"dual burden"]),
            ("Official non-cooperation", [r"official", r"officer", r"not take serious", r"not take her"]),
            ("Traditional leader dominance", [r"traditional", r"pradhan", r"parha", r"more powerful"]),
            ("Family opposition", [r"family", r"husband", r"support"]),
            ("No specific difficulty", [r"same", r"nothing special", r"others"]),
        ],
    },
    # ----------------- Traditional Leader -----------------
    {
        "respondent_group": "Traditional Leader",
        "question_no": 17,
        "question_contains": "experience working",
        "themes": [
            ("Positive/cooperative", [r"good", r"positive", r"cooperat", r"support", r"work well"]),
            ("Women less confident/experienced", [r"confidence", r"experience", r"hesitant", r"shy"]),
            ("Male/family interference", [r"husband", r"family", r"male", r"not independent"]),
            ("Traditional/formal tension", [r"tension", r"conflict", r"formal", r"traditional"]),
            ("No major issue", [r"no problem", r"no issue", r"fine", r"same"]),
        ],
    },
    {
        "respondent_group": "Traditional Leader",
        "question_no": 20,
        "question_contains": "actual decisions",
        "themes": [
            ("Yes, proxy exists", [r"__STARTS_WITH_YES__", r"interference", r"husband", r"taken by"]),
            ("No, women decide", [r"__STARTS_WITH_NO__", r"woman", r"herself", r"independent"]),
            ("Sometimes/mixed", [r"sometimes", r"some", r"mixed"]),
        ],
    },
    {
        "respondent_group": "Traditional Leader",
        "question_no": 16,
        "question_contains": "effective as leaders",
        "themes": [
            ("Yes, equally/more effective", [r"yes", r"equal", r"more", r"good"]),
            ("No, less effective", [r"no", r"less", r"not effective"]),
            ("Depends on training/support", [r"training", r"support", r"experience", r"depends"]),
            ("Mixed/strengths and weaknesses", [r"mixed", r"some", r"both", r"strength", r"weakness"]),
        ],
    },
]


# %%
# Step 4: Load cleaned responses and apply thematic coding

analysis_rows = pd.read_csv(CLEANED_ANALYSIS_PATH)
print(f"Loaded {len(analysis_rows):,} cleaned analysis rows")

# Filter to nonblank, non-profile responses for thematic coding
profile_keywords = ["name", "village", "panchayat", "block", "district"]
analysis_rows["question_key"] = analysis_rows["Question"].astype(str).str.lower()
analysis_rows["is_profile"] = analysis_rows["question_key"].apply(
    lambda q: any(kw in q for kw in profile_keywords)
)
coding_pool = analysis_rows[~analysis_rows["is_profile"]].copy()

# Exclude missing/blank responses from thematic coding pool.
# These have no substantive content to code and would otherwise inflate the
# denominator or appear as "Other/uncoded".
missing_like_values = {
    "",
    "-",
    "na",
    "n a",
    "not available",
    "not mentioned",
    "none",
    "no response",
    "do not know",
    "don't know",
    "dont know",
    "i don't know",
    "i dont know",
    "not mentioned/do not know",
}
coding_pool["is_missing_like"] = coding_pool["response_clean"].astype(str).str.strip().str.lower().isin(missing_like_values)
coding_pool = coding_pool[~coding_pool["is_missing_like"]].copy()

# Identify high-fragmentation questions for reference
fragmentation = (
    coding_pool.groupby(["respondent_group", "Question No", "Question"])
    .agg(
        responses=("response_clean", "size"),
        unique=("response_clean", "nunique"),
    )
    .reset_index()
)
fragmentation["fragmentation_ratio"] = fragmentation["unique"] / fragmentation["responses"]
high_frag = fragmentation[
    (fragmentation["unique"] >= 5) | (fragmentation["fragmentation_ratio"] >= 0.5)
].sort_values("unique", ascending=False)

print(f"\nHigh-fragmentation open-ended questions: {len(high_frag)}")
display(high_frag.head(20))


# %%
# Step 5: Apply coding rules

coded_rows = []
review_rows = []

for rule in THEMATIC_RULES:
    group = rule["respondent_group"]
    q_no = rule["question_no"]
    q_contains = rule["question_contains"]
    themes = rule["themes"]

    # Select rows for this question
    mask = (
        (coding_pool["respondent_group"] == group)
        & (coding_pool["Question No"] == q_no)
        & (coding_pool["question_key"].str.contains(q_contains, regex=False))
    )
    question_rows = coding_pool[mask].copy()

    if len(question_rows) == 0:
        print(f"No rows found for {group} Q{q_no} ({q_contains})")
        continue

    question_text = question_rows["Question"].iloc[0]
    print(f"\nCoding {group} Q{q_no}: {question_text[:80]}... ({len(question_rows)} responses)")

    # Apply rules to each response
    for _, row in question_rows.iterrows():
        text = normalize(row["response_clean"])
        matched_themes = []
        for theme_label, patterns in themes:
            # Handle special starts-with markers
            has_special = False
            if "__STARTS_WITH_YES__" in patterns:
                has_special = True
                if starts_with_any(text, [r"yes\b"]):
                    matched_themes.append(theme_label)
                    continue
            if "__STARTS_WITH_NO__" in patterns:
                has_special = True
                if starts_with_any(text, [r"no\b"]):
                    matched_themes.append(theme_label)
                    continue
            # Standard regex patterns
            real_patterns = [p for p in patterns if not p.startswith("__")]
            if real_patterns and contains_any(text, real_patterns):
                matched_themes.append(theme_label)

        if not matched_themes:
            matched_themes = ["Other/uncoded"]
            review_rows.append({
                "respondent_group": group,
                "question_no": q_no,
                "question": question_text,
                "respondent_id": row["respondent_id"],
                "response_text": row["response_text"],
                "response_clean": row["response_clean"],
                "suggested_themes": "; ".join(matched_themes),
            })

        for theme in matched_themes:
            coded_rows.append({
                "respondent_group": group,
                "question_no": q_no,
                "question": question_text,
                "respondent_id": row["respondent_id"],
                "response_text": row["response_text"],
                "response_clean": row["response_clean"],
                "theme": theme,
            })

coded_df = pd.DataFrame(coded_rows)
review_df = pd.DataFrame(review_rows)

print(f"\nTotal coded theme mentions: {len(coded_df):,}")
print(f"Responses needing manual review: {len(review_df):,}")


# %%
# Step 6: Build thematic frequency tables

theme_frequencies = []

for (group, q_no, question, theme), group_df in coded_df.groupby(
    ["respondent_group", "question_no", "question", "theme"], dropna=False
):
    # Denominator = number of respondents who answered this question
    rule_match = next(
        (r for r in THEMATIC_RULES if r["respondent_group"] == group and r["question_no"] == q_no),
        None,
    )
    if rule_match is None:
        continue
    denominator = coding_pool[
        (coding_pool["respondent_group"] == group)
        & (coding_pool["Question No"] == q_no)
        & (coding_pool["question_key"].str.contains(rule_match["question_contains"], regex=False))
    ]["respondent_id"].nunique()

    theme_frequencies.append({
        "respondent_group": group,
        "question_no": q_no,
        "question": question,
        "theme": theme,
        "count": len(group_df),
        "denominator_n": denominator,
        "percent_of_respondents": round(len(group_df) / denominator * 100, 2),
    })

theme_freq_df = pd.DataFrame(theme_frequencies)
theme_freq_df = theme_freq_df.sort_values(["respondent_group", "question_no", "count"], ascending=[True, True, False])

print("\nThematic frequency tables (top 30):")
display(theme_freq_df.head(30))


# %%
# Step 7: Build thematic summary by question

theme_summary_rows = []
for (group, q_no, question), group_df in theme_freq_df.groupby(
    ["respondent_group", "question_no", "question"], dropna=False
):
    top = group_df.sort_values("count", ascending=False).iloc[0]
    theme_summary_rows.append({
        "respondent_group": group,
        "question_no": q_no,
        "question": question,
        "denominator_n": top["denominator_n"],
        "number_of_themes": len(group_df),
        "top_theme": top["theme"],
        "top_count": top["count"],
        "top_percent": top["percent_of_respondents"],
    })

theme_summary_df = pd.DataFrame(theme_summary_rows).sort_values(["respondent_group", "question_no"])

print("\nThematic summary by question:")
display(theme_summary_df)


# %%
# Step 8: Create review workbook with visible, valid sheet names

review_workbook_path = REVIEW_DIR / "thematic_coding_review.xlsx"
try:
    with pd.ExcelWriter(review_workbook_path, engine="openpyxl") as writer:
        # Summary sheets first (visible)
        theme_summary_df.to_excel(writer, sheet_name="Summary", index=False)
        theme_freq_df.to_excel(writer, sheet_name="All Themes", index=False)
        review_df.to_excel(writer, sheet_name="Needs Review", index=False)

        # One sheet per question with coded responses (one row per respondent, one theme per row)
        for (group, q_no, question), q_df in coded_df.groupby(
            ["respondent_group", "question_no", "question"], dropna=False
        ):
            sheet_name = safe_sheet_name(f"{group[:10]}_Q{q_no}")
            # Sort to keep respondent_id ordered and avoid index issues
            q_df = q_df.sort_values(["respondent_id", "theme"])
            q_df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\nSaved review workbook: {review_workbook_path}")
except Exception as e:
    print(f"Could not write review workbook: {e}")
    # Save CSVs as fallback
    theme_summary_df.to_csv(REVIEW_DIR / "theme_summary.csv", index=False)
    theme_freq_df.to_csv(REVIEW_DIR / "theme_frequencies.csv", index=False)
    review_df.to_csv(REVIEW_DIR / "needs_review.csv", index=False)


# %%
# Step 9: Save thematic coding outputs

coded_df.to_csv(OUTPUT_DIR / "thematic_coded_responses.csv", index=False)
theme_freq_df.to_csv(OUTPUT_DIR / "thematic_frequencies.csv", index=False)
theme_summary_df.to_csv(OUTPUT_DIR / "thematic_summary.csv", index=False)
review_df.to_csv(OUTPUT_DIR / "thematic_needs_review.csv", index=False)

print("\nSaved thematic coding outputs to:")
print(OUTPUT_DIR)
