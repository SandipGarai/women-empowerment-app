# %%
# Step 1: Import libraries and define paths
# This script expands selected survey questions into multi-response indicators.
# Multi-response means one respondent can be counted in more than one category.

from pathlib import Path
import re
import sys
import unicodedata

import pandas as pd


# Keep terminal output readable on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from IPython.display import display
except ImportError:
    display = print


PROJECT_DIR = Path(__file__).resolve().parent
CLEANED_DIR = PROJECT_DIR / "outputs" / "cleaned"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "multi_response"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLEANED_ANALYSIS_PATH = CLEANED_DIR / "cleaned_analysis_responses.csv"


# %%
# Step 2: Load cleaned analysis responses
# This file comes from 02_clean_and_code_surveys.py.

analysis_rows = pd.read_csv(CLEANED_ANALYSIS_PATH)

print(f"Cleaned analysis rows loaded: {len(analysis_rows):,}")
display(analysis_rows.head(10))


# %%
# Step 3: Helper functions
# These functions normalize text and make category detection more consistent.

def normalize_text(value):
    """Normalize punctuation, spacing, and case for matching."""
    text = "" if pd.isna(value) else str(value)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\u2010\u2011\u2012\u2013\u2014\u2212]", "-", text)
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def key_text(value):
    """Create a lowercase matching key."""
    text = normalize_text(value).lower()
    text = re.sub(r"[,+;/().:]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def has_any(text, patterns):
    """Return True if any plain substring or regex pattern matches."""
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False


def add_indicator(rows, row, indicator, label, evidence, note):
    """Append one indicator record."""
    rows.append(
        {
            "respondent_group": row["respondent_group"],
            "respondent_id": row["respondent_id"],
            "question_no": row["Question No"],
            "section": row["Section"],
            "particular": row["Particular"],
            "question": row["Question"],
            "indicator": indicator,
            "indicator_label": label,
            "present": 1,
            "response_clean": row["response_clean"],
            "response_text": row["response_text"],
            "coding_note": note,
            "evidence": evidence,
        }
    )


# %%
# Step 4: Define multi-response coding rules
# Each function receives one cleaned row and returns zero or more indicator records.

def code_info_sources(row):
    """Code 'How do you get info on schemes?' into source indicators."""
    rows = []
    text = key_text(row["response_clean"])

    # Treat "All"/"All sources" as all core local information channels.
    if text in {"all", "all sources", "all source", "every source"}:
        for indicator, label in [
            ("info_mukhiya_ward", "Mukhiya/Ward member"),
            ("info_friends_neighbours", "Friends/neighbours"),
            ("info_asha_anganwadi", "ASHA/Anganwadi"),
            ("info_digital_social_media", "Digital/social media"),
        ]:
            add_indicator(rows, row, indicator, label, "All", "expanded_all_core_channels")
        return rows

    if has_any(text, [r"i don'?t get any information", r"no information",
                      r"^no source", r"^none$", r"^nothing$"]):
        add_indicator(
            rows,
            row,
            "info_no_information",
            "No information received",
            row["response_clean"],
            "coded_no_information",
        )
        return rows

    if has_any(text, [r"mukhiya", r"ward"]):
        add_indicator(rows, row, "info_mukhiya_ward", "Mukhiya/Ward member", row["response_clean"], "coded_info_source")
    if has_any(text, [r"friend", r"neighbour", r"neighbor"]):
        add_indicator(rows, row, "info_friends_neighbours", "Friends/neighbours", row["response_clean"], "coded_info_source")
    if has_any(text, [r"asha", r"angan"]):
        add_indicator(rows, row, "info_asha_anganwadi", "ASHA/Anganwadi", row["response_clean"], "coded_info_source")
    if has_any(text, [r"whatsapp", r"digital", r"social media"]):
        add_indicator(rows, row, "info_digital_social_media", "Digital/social media", row["response_clean"], "coded_info_source")
    if has_any(text, [r"government", r"govt", r"official"]):
        add_indicator(rows, row, "info_government_officials", "Government officials", row["response_clean"], "coded_info_source")

    return rows


def code_contact_modes(row):
    """Code 'How do you contact Mukhiya?' into contact-mode indicators."""
    rows = []
    text = key_text(row["response_clean"])

    if has_any(text, [r"visit", r"house", r"go to", r"direct"]):
        add_indicator(rows, row, "contact_visit", "Visit/direct visit", row["response_clean"], "coded_contact_mode")
    if has_any(text, [r"phone", r"call", r"mobile"]):
        add_indicator(rows, row, "contact_phone", "Phone call", row["response_clean"], "coded_contact_mode")
    if has_any(text, [r"someone", r"through"]):
        add_indicator(rows, row, "contact_through_someone", "Through someone else", row["response_clean"], "coded_contact_mode")

    return rows


def code_difficulties(row):
    """Code women's leadership difficulties into thematic indicators."""
    rows = []
    text = key_text(row["response_clean"])

    # "no difficulty" must be tested before anything else, otherwise a
    # respondent who reports no problem is silently dropped from the table.
    if has_any(text, [r"\bno difficulty\b", r"\bno problem\b", r"not mentioned",
                      r"do not know", r"nothing special", r"\bsame\b"]):
        add_indicator(rows, row, "difficulty_none_unsure", "None/unsure/not specified", row["response_clean"], "coded_difficulty")
        return rows

    # NOTE on "Lack of Support from Men": this is the most common answer in the
    # General Public sheet. It must be counted as a men/patriarchy difficulty.
    # The family/husband rule below therefore no longer matches a bare "support",
    # which used to swallow this answer into the wrong category.
    if has_any(text, [r"men don'?t listen", r"village men", r"\bmen\b", r"patriarch", r"\bmale\b"]):
        add_indicator(rows, row, "difficulty_men_patriarchy", "Men do not listen/patriarchy", row["response_clean"], "coded_difficulty")
    if has_any(text, [r"housework", r"houshold", r"household", r"dual burden"]):
        add_indicator(rows, row, "difficulty_household_work", "Household work/dual burden", row["response_clean"], "coded_difficulty")
    if has_any(text, [r"officer", r"official", r"cooperate", r"seriously"]):
        add_indicator(rows, row, "difficulty_officials_not_serious", "Officials do not take seriously/cooperate", row["response_clean"], "coded_difficulty")
    if has_any(text, [r"traditional", r"pradhan", r"powerfull", r"powerful"]):
        add_indicator(rows, row, "difficulty_traditional_power", "Traditional Pradhan power", row["response_clean"], "coded_difficulty")
    if has_any(text, [r"\bfamily\b", r"husband", r"permission", r"in laws", r"relatives"]):
        add_indicator(rows, row, "difficulty_family_husband", "Family/husband permission or support", row["response_clean"], "coded_difficulty")
    if has_any(text, [r"\bother", r"others"]):
        add_indicator(rows, row, "difficulty_other", "Other difficulty", row["response_clean"], "coded_difficulty")

    return rows


def code_kharif_crops(row):
    """Code Kharif crop names into crop indicators."""
    rows = []
    text = key_text(row["response_clean"])

    crop_patterns = [
        ("kharif_paddy", "Paddy", [r"paddy", r"pady"]),
        ("kharif_ragi_mandua", "Ragi/Mandua/Finger millet", [r"ragi", r"mandua", r"finger millet"]),
        ("kharif_maize", "Maize", [r"maize"]),
        ("kharif_arhar", "Arhar", [r"arhar"]),
        ("kharif_lentil_masoor", "Lentil/Masoor", [r"lentil", r"masoor"]),
        ("kharif_linseed", "Linseed", [r"linseed"]),
        ("kharif_tomato", "Tomato", [r"tomato"]),
        ("kharif_brinjal", "Brinjal", [r"brinjal"]),
        ("kharif_wheat", "Wheat", [r"wheat"]),
        ("kharif_kodo_millet", "Kodo millet", [r"kodo"]),
        ("kharif_jowar_sorghum", "Jowar/Sorghum", [r"jowar", r"sorghum"]),
        ("kharif_moong", "Moong/Mung", [r"moong", r"mung"]),
        ("kharif_ginger", "Ginger", [r"ginger"]),
        ("kharif_urad", "Urad", [r"urad"]),
        ("kharif_groundnut", "Groundnut", [r"groundnut"]),
        ("kharif_vegetables", "Vegetables", [r"vegetable"]),
        ("kharif_sugarcane", "Sugarcane", [r"sugarcane"]),
        ("kharif_sesame", "Sesame", [r"sesame"]),
    ]

    for indicator, label, patterns in crop_patterns:
        if has_any(text, patterns):
            add_indicator(rows, row, indicator, label, row["response_clean"], "coded_kharif_crop")

    return rows


def code_rabi_crops(row):
    """Code Rabi crop names into crop indicators."""
    rows = []
    text = key_text(row["response_clean"])

    crop_patterns = [
        ("rabi_wheat", "Wheat", [r"wheat"]),
        ("rabi_pea", "Pea/Peas", [r"\bpea\b", r"\bpeas\b"]),
        ("rabi_mustard", "Mustard/Sarson", [r"mustard", r"sarson"]),
        ("rabi_potato", "Potato", [r"potato"]),
        ("rabi_gram_chana", "Gram/Chana", [r"\bgram\b", r"chana"]),
        ("rabi_beans", "Beans", [r"bean"]),
        ("rabi_onion", "Onion", [r"onion"]),
        ("rabi_lentil_masoor", "Lentil/Masoor", [r"lentil", r"masoor"]),
        ("rabi_bottle_gourd", "Bottle gourd", [r"bottle gourd"]),
        ("rabi_tomato", "Tomato", [r"tomato"]),
        ("rabi_spinach", "Spinach", [r"spinach"]),
        ("rabi_garlic", "Garlic", [r"garlic"]),
        ("rabi_soybean", "Soybean", [r"soybean"]),
        ("rabi_maize", "Maize", [r"maize"]),
        ("rabi_vegetables", "Vegetables", [r"vegetable"]),
        ("rabi_chilli", "Chilli", [r"chilli", r"chili"]),
        ("rabi_cauliflower", "Cauliflower", [r"caulif"]),
        # Added after reviewing uncoded responses in the Sept 2026 workbook
        ("rabi_barley", "Barley/Jau", [r"barley", r"\bjau\b"]),
        ("rabi_capsicum", "Capsicum", [r"capsicum"]),
        ("rabi_flaxseed", "Flaxseed/Linseed/Alsi", [r"flaxseed", r"linseed", r"\balsi\b"]),
        ("rabi_niger", "Niger/Surguja", [r"surguja", r"surjuga", r"niger"]),
        ("rabi_coriander", "Coriander/Dhania", [r"coriander", r"dhania"]),
        ("rabi_radish", "Radish/Mooli", [r"radish", r"mooli"]),
        ("rabi_carrot", "Carrot", [r"carrot"]),
        ("rabi_cabbage", "Cabbage", [r"cabbage"]),
        ("rabi_brinjal", "Brinjal", [r"brinjal", r"eggplant"]),
        ("rabi_sugarcane", "Sugarcane", [r"sugarcane"]),
    ]

    for indicator, label, patterns in crop_patterns:
        if has_any(text, patterns):
            add_indicator(rows, row, indicator, label, row["response_clean"], "coded_rabi_crop")

    return rows


def code_livestock(row):
    """Code livestock into animal indicators."""
    rows = []
    text = key_text(row["response_clean"])

    if has_any(text, [r"not mentioned", r"do not know", r"^no$"]):
        add_indicator(rows, row, "livestock_none_unsure", "None/not mentioned", row["response_clean"], "coded_livestock")
        return rows

    if text == "yes":
        add_indicator(rows, row, "livestock_yes_unspecified", "Livestock available, type unspecified", row["response_clean"], "coded_livestock_unspecified")
        return rows

    if re.fullmatch(r"\d+(?:\.0)?", text):
        add_indicator(rows, row, "livestock_count_only", "Livestock count reported only", row["response_clean"], "coded_livestock_count_only")
        return rows

    animal_patterns = [
        ("livestock_goat", "Goat", [r"goat"]),
        ("livestock_cow", "Cow", [r"\bcow\b"]),
        ("livestock_buffalo", "Buffalo", [r"buffalo"]),
        ("livestock_bull", "Bull", [r"\bbull\b"]),
        ("livestock_chicken_hen", "Chicken/Hen", [r"chicken", r"\bhen\b", r"hens"]),
        ("livestock_duck", "Duck", [r"duck"]),
        ("livestock_pig", "Pig", [r"\bpig\b"]),
    ]

    for indicator, label, patterns in animal_patterns:
        if has_any(text, patterns):
            add_indicator(rows, row, indicator, label, row["response_clean"], "coded_livestock")

    return rows


def code_agriculture_techniques(row):
    """Code agriculture techniques into technique indicators."""
    rows = []
    text = key_text(row["response_clean"])

    if has_any(text, [r"not mentioned", r"do not know", r"no technique", r"^no$"]):
        add_indicator(rows, row, "tech_none_unsure", "None/not mentioned", row["response_clean"], "coded_agri_technique")
        return rows

    technique_patterns = [
        ("tech_drip_irrigation", "Drip irrigation", [r"drip"]),
        ("tech_irrigation_pump_boring", "Irrigation/pump/boring", [r"irrigation", r"motor", r"pump", r"boring", r"सींच"]),
        ("tech_river_irrigation", "River irrigation/source", [r"\briver\b"]),
        ("tech_solar_irrigation", "Solar irrigation/panel", [r"solar", r"pannel", r"panel"]),
        ("tech_tractor_machine", "Tractor/machine/tools", [r"tractor", r"machine", r"\btool\b"]),
        ("tech_seed_treatment", "Seed treatment", [r"seed treatment"]),
        ("tech_soil_test", "Soil test", [r"soil test"]),
        ("tech_bed_planting", "Bed planting", [r"bed planting"]),
        ("tech_sri", "SRI technology", [r"\bsri\b", r"system of rice intensification"]),
        ("tech_vermicompost", "Vermicompost", [r"vermicompost"]),
        ("tech_integrated_farming", "Integrated farming", [r"integrated farming"]),
        ("tech_poultry_goat_rearing", "Poultry/goat rearing", [r"poultry", r"goat rearing"]),
        ("tech_synthetic_fertilizer", "Synthetic fertilizer", [r"synthetic fertilizer"]),
        ("tech_mango_gardening", "Mango gardening", [r"mango"]),
    ]

    for indicator, label, patterns in technique_patterns:
        if has_any(text, patterns):
            add_indicator(rows, row, indicator, label, row["response_clean"], "coded_agri_technique")

    return rows


# %%
# Step 5: Apply the multi-response rules to selected questions
# The matching is based on question text, so the script remains readable.

indicator_rows = []
unmatched_selected_rows = []

# Question-text fragments that identify a multi-response question. Used both to
# dispatch a coder and to decide whether an unmatched response deserves an
# explicit "Uncoded" indicator.
MULTI_RESPONSE_QUESTION_KEYS = {
    "how do you get info on schemes",
    "how do you contact mukhiya",
    "biggest difficulty",
    "kharif crops",
    "rabi crops",
    "livestock",
    "best technique",
}

for _, row in analysis_rows.iterrows():
    question_key = key_text(row["Question"])
    row_indicators = []

    if "how do you get info on schemes" in question_key:
        row_indicators = code_info_sources(row)
    elif "how do you contact mukhiya" in question_key:
        row_indicators = code_contact_modes(row)
    elif "biggest difficulty" in question_key:
        row_indicators = code_difficulties(row)
    elif "kharif crops" in question_key:
        row_indicators = code_kharif_crops(row)
    elif "rabi crops" in question_key:
        row_indicators = code_rabi_crops(row)
    elif "livestock" in question_key:
        row_indicators = code_livestock(row)
    elif "best technique" in question_key:
        row_indicators = code_agriculture_techniques(row)

    # SAFETY NET: if a response belongs to a multi-response question but matched
    # no rule, record it explicitly as "Uncoded" rather than dropping it. Without
    # this, counts quietly fall short of the denominator and the gap only shows
    # up as a validation warning that is easy to miss.
    if row_indicators is not None and len(row_indicators) == 0 and any(k in question_key for k in MULTI_RESPONSE_QUESTION_KEYS):
        add_indicator(
            row_indicators, row, "uncoded_response",
            "Uncoded - needs manual review", row["response_clean"], "coded_uncoded",
        )

    indicator_rows.extend(row_indicators)

    # Keep a review list of selected question rows that did not trigger any indicator.
    if (
        "info on schemes" in question_key
        or "contact mukhiya" in question_key
        or "biggest difficulty" in question_key
        or "kharif crops" in question_key
        or "rabi crops" in question_key
        or "livestock" in question_key
        or "best technique" in question_key
    ) and not row_indicators:
        unmatched_selected_rows.append(row)

multi_response_long = pd.DataFrame(indicator_rows)
unmatched_selected = pd.DataFrame(unmatched_selected_rows)

print(f"Multi-response indicator rows: {len(multi_response_long):,}")
print(f"Selected rows needing review: {len(unmatched_selected):,}")
display(multi_response_long.head(20))


# %%
# Step 6: Build respondent-level wide indicator data
# Each row is one respondent-question. Indicator columns are 0/1.

indicator_index_columns = [
    "respondent_group",
    "respondent_id",
    "question_no",
    "section",
    "particular",
    "question",
]

if len(multi_response_long) > 0:
    multi_response_wide = (
        multi_response_long.pivot_table(
            index=indicator_index_columns,
            columns="indicator",
            values="present",
            aggfunc="max",
            fill_value=0,
        )
        .reset_index()
    )

    # Remove the column-axis name left by pivot_table.
    multi_response_wide.columns.name = None
else:
    multi_response_wide = pd.DataFrame(columns=indicator_index_columns)

display(multi_response_wide.head(20))


# %%
# Step 7: Create count and percent summaries
# Denominator is number of respondents with a nonblank answer for that question.
# Percentages can add to more than 100 because responses are multi-coded.

selected_question_keys = [
    "how do you get info on schemes",
    "how do you contact mukhiya",
    "biggest difficulty",
    "kharif crops",
    "rabi crops",
    "livestock",
    "best technique",
]

selected_rows = analysis_rows[
    analysis_rows["Question"].apply(
        lambda value: any(key in key_text(value) for key in selected_question_keys)
    )
].copy()

denominators = (
    selected_rows.groupby(["respondent_group", "Question No", "Question"], dropna=False)
    .agg(respondents_with_answer=("respondent_id", "nunique"))
    .reset_index()
    .rename(columns={"Question No": "question_no", "Question": "question"})
)

multi_response_summary = (
    multi_response_long.groupby(
        ["respondent_group", "question_no", "question", "indicator", "indicator_label"],
        dropna=False,
    )
    .agg(count=("respondent_id", "nunique"))
    .reset_index()
    .merge(denominators, on=["respondent_group", "question_no", "question"], how="left")
)

multi_response_summary["percent_of_respondents"] = (
    multi_response_summary["count"]
    / multi_response_summary["respondents_with_answer"]
    * 100
).round(2)

multi_response_summary = multi_response_summary.sort_values(
    ["respondent_group", "question_no", "count"],
    ascending=[True, True, False],
)

display(multi_response_summary.head(60))


# %%
# Step 8: Create an unmatched-response review table
# This file tells us what the rule set did not yet understand.

if len(unmatched_selected) > 0:
    unmatched_review = (
        unmatched_selected.groupby(
            [
                "respondent_group",
                "Question No",
                "Question",
                "response_clean",
                "response_text",
            ],
            dropna=False,
        )
        .size()
        .reset_index(name="count")
        .sort_values(["respondent_group", "Question No", "count"], ascending=[True, True, False])
    )
else:
    unmatched_review = pd.DataFrame(
        columns=[
            "respondent_group",
            "Question No",
            "Question",
            "response_clean",
            "response_text",
            "count",
        ]
    )

display(unmatched_review.head(50))


# %%
# Step 9: Save outputs
# These files are the corrected basis for multi-response analysis and charts.

multi_response_long.to_csv(OUTPUT_DIR / "multi_response_long.csv", index=False)
multi_response_wide.to_csv(OUTPUT_DIR / "multi_response_wide.csv", index=False)
multi_response_summary.to_csv(OUTPUT_DIR / "multi_response_summary.csv", index=False)
unmatched_review.to_csv(OUTPUT_DIR / "multi_response_unmatched_review.csv", index=False)

print("Saved multi-response outputs to:")
print(OUTPUT_DIR)
