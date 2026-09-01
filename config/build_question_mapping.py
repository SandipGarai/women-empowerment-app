# %%
# Rebuild config/question_hypothesis_mapping.csv from the current workbook.
#
# WHY THIS EXISTS
# ---------------
# The mapping tells the pipeline which survey question supports which synopsis
# objective and hypothesis. Writing it as raw question numbers means it silently
# rots every time the workbook is renumbered: in the September 2026 update the
# Traditional Leader sheet shifted by +2 from Q20 onward, which would have
# pointed a dozen ICT questions at the wrong objective without any error.
#
# So the mapping is declared here against a distinctive PHRASE from each question,
# and the actual question number is looked up from the cleaned data. Renumber the
# workbook, re-run this script, and the CSV is correct again.
#
# Run:  python config/build_question_mapping.py
# Then re-run the pipeline from 09 (or from 02 for a full refresh).

from pathlib import Path
import re
import sys

import pandas as pd


CONFIG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CONFIG_DIR.parent
CLEANED_PATH = PROJECT_DIR / "outputs" / "cleaned" / "cleaned_analysis_responses.csv"
OUTPUT_CSV = CONFIG_DIR / "question_hypothesis_mapping.csv"


OBJECTIVES = {
    "O1": ("Obj 1: 73rd Amendment impact on representation & participation",
           "H1: 73rd Amendment increased representation/participation \u2192 empowerment"),
    "O2": ("Obj 2: Effectiveness of capacity building initiatives",
           "H2: Capacity building enhances participation & empowerment"),
    "O3": ("Obj 3: Role of ICT in promoting participation",
           "H3: ICT played a crucial role"),
    "O4": ("Obj 4: Participation \u2192 empowerment & community development",
           "H4: Participation contributed to empowerment & community development"),
}


# (respondent_group, distinctive phrase from the question, [objective codes])
#
# Deliberately NOT mapped: name/age/education/caste/occupation/landholding and the
# agriculture block. Those describe the sample and belong in the synopsis chapter
# "Socio Economic profile of the respondents", not to any objective.

MAPPING_SPEC = [
    # ---------------- Women Representative (n=8) ----------------
    ("Women Representative", "position held", ["O1"]),
    ("Women Representative", "previous political/community leadership", ["O1"]),
    ("Women Representative", "what motivated you to contest", ["O1"]),
    ("Women Representative", "opposition from your family or community", ["O1"]),
    ("Women Representative", "how often do you attend gram sabha", ["O1"]),
    ("Women Representative", "comfortable do you feel speaking", ["O1"]),
    # Involvement battery (1-5 scale)
    ("Women Representative", "involvement in activities: planning of development", ["O1", "O4"]),
    ("Women Representative", "involvement in activities: discussing the budget", ["O1", "O4"]),
    ("Women Representative", "involvement in activities: monitoring the implementation", ["O1", "O4"]),
    ("Women Representative", "involvement in activities: solving domestic", ["O1", "O4"]),
    ("Women Representative", "opinion is heard and considered by male colleagues", ["O1", "O4"]),
    # Challenges battery (1-5 scale)
    ("Women Representative", "challenges you face: lack of cooperation from male", ["O1"]),
    ("Women Representative", "challenges you face: interference from husband", ["O1"]),
    ("Women Representative", "challenges you face: lack of support from government", ["O1"]),
    ("Women Representative", "challenges you face: lack of knowledge about rules", ["O1", "O2"]),
    ("Women Representative", "challenges you face: dual burden", ["O1"]),
    ("Women Representative", "challenges you face: restrictions from traditional", ["O1", "O4"]),
    ("Women Representative", "challenges you face: lack of transportation", ["O1"]),
    ("Women Representative", "challenges you face: threats or verbal abuse", ["O1"]),
    ("Women Representative", "what is the biggest challenge you face?", ["O1"]),
    # Empowerment change battery
    ("Women Representative", "change in: a. your confidence", ["O4"]),
    ("Women Representative", "change in: b. your mobility", ["O4"]),
    ("Women Representative", "change in: c. decision-making power", ["O4"]),
    ("Women Representative", "change in: d. respect from your family", ["O4"]),
    ("Women Representative", "raise issues related to women", ["O4"]),
    # Traditional vs formal governance
    ("Women Representative", "aware of the traditional parha panchayat", ["O4"]),
    ("Women Representative", "interacted with the mahto or pahan", ["O4"]),
    ("Women Representative", "nature of the interaction", ["O4"]),
    ("Women Representative", "which system (gram panchayat or parha", ["O4"]),
    # ICT
    ("Women Representative", "do you have a personal mobile phone", ["O3"]),
    ("Women Representative", "communicate with villagers about panchayat work", ["O3"]),
    ("Women Representative", "receive information and circulars from the block", ["O3"]),
    ("Women Representative", "how useful is your phone for your work", ["O3"]),
    ("Women Representative", "training on how to use a computer or smartphone", ["O2", "O3"]),
    ("Women Representative", "biggest challenges you face in using icts", ["O3"]),

    # ---------------- Govt Officials (n=11) ----------------
    ("Govt Officials", "major differences do you see when working with male", ["O1"]),
    ("Govt Officials", "require different kinds of training or support", ["O2"]),
    ("Govt Officials", "biggest administrative hurdles", ["O2"]),
    ("Govt Officials", "parallel traditional tribal governance system", ["O4"]),
    ("Govt Officials", "initiatives from the district or state administration to mentor", ["O2"]),
    ("Govt Officials", "reservation has been successful in empowering women", ["O1", "O4"]),
    ("Govt Officials", "primary digital channels", ["O3"]),
    ("Govt Officials", "are such digital channels effective", ["O3"]),
    ("Govt Officials", "gaps between male and female representatives in their access", ["O3"]),
    ("Govt Officials", "digital literacy training programs", ["O2", "O3"]),
    ("Govt Officials", "do you see a need for such training", ["O2"]),
    ("Govt Officials", "digital attendance for mgnrega", ["O3", "O4"]),

    # ---------------- Mahila Mukhiya (n=8) ----------------
    ("Mahila Mukhiya", "any previous political/community leadership", ["O1"]),
    ("Mahila Mukhiya", "how you became mukhiya", ["O1"]),
    ("Mahila Mukhiya", "important decision you made", ["O4"]),
    ("Mahila Mukhiya", "influence of their husbands", ["O1", "O4"]),
    ("Mahila Mukhiya", "relationship with traditional/local leaders", ["O4"]),
    ("Mahila Mukhiya", "authority clashed with their authority", ["O4"]),
    ("Mahila Mukhiya", "how do government officials (such as bdo", ["O1"]),
    ("Mahila Mukhiya", "for what purposes do you use your phone", ["O3"]),
    ("Mahila Mukhiya", "help you in using the phone", ["O3"]),
    ("Mahila Mukhiya", "mobile phone changed your access to information", ["O3"]),
    ("Mahila Mukhiya", "what kind of technology training", ["O2", "O3"]),
    ("Mahila Mukhiya", "what special challenges do you face", ["O1"]),
    ("Mahila Mukhiya", "most proud of", ["O4"]),
    ("Mahila Mukhiya", "wanted to do but could not", ["O4"]),
    ("Mahila Mukhiya", "young girl wants to enter politics", ["O4"]),

    # ---------------- Traditional Leader (n=5) ----------------
    ("Traditional Leader", "opinion on the policy of reserving seats", ["O1"]),
    ("Traditional Leader", "women are effective as leaders compared to men", ["O1"]),
    ("Traditional Leader", "experience working with women representatives", ["O1"]),
    ("Traditional Leader", "traditional roles of oraon women changed", ["O4"]),
    ("Traditional Leader", "which matters should the gram panchayat handle", ["O4"]),
    ("Traditional Leader", "matters should the traditional (parha) panchayat handle", ["O4"]),
    ("Traditional Leader", "change after the strengthening of panchayati raj", ["O1", "O4"]),
    ("Traditional Leader", "actual decisions of women representatives are taken by their husbands", ["O1", "O4"]),
    ("Traditional Leader", "any woman can become a traditional leader", ["O4"]),
    ("Traditional Leader", "how do you use mobile phones for your panchayat work", ["O3"]),
    ("Traditional Leader", "use technology (internet, computer, phone, sms) differently", ["O3"]),
    ("Traditional Leader", "same access to smartphones and data", ["O3"]),
    ("Traditional Leader", "mobile phone in a woman's hand makes her more independent", ["O3", "O4"]),
    ("Traditional Leader", "prefer using whatsapp or other technical messaging", ["O3"]),
    ("Traditional Leader", "communication technologies as a traditional leader", ["O3"]),
    ("Traditional Leader", "resolve issues through phone calls or whatsapp instead", ["O3"]),
    ("Traditional Leader", "icts (information and communication technologies) strengthen", ["O3"]),
    ("Traditional Leader", "information and news reached people only through you", ["O3"]),
    ("Traditional Leader", "when elected women members use icts", ["O3"]),

    # ---------------- General Public (n=53) ----------------
    ("General Public", "do you know who the mukhiya is", ["O1"]),
    ("General Public", "mukhiya gender", ["O1"]),
    ("General Public", "would you go to mukhiya for a problem", ["O4"]),
    ("General Public", "did they help", ["O4"]),
    ("General Public", "mobile phone?", ["O3"]),
    ("General Public", "how do you get info on schemes", ["O3"]),
    ("General Public", "how do you contact mukhiya", ["O3"]),
    ("General Public", "can a woman be a good mukhiya", ["O4"]),
    ("General Public", "biggest difficulty", ["O4"]),
    ("General Public", "improvements under woman mukhiya", ["O4"]),
    ("General Public", "are icts helpful", ["O3"]),
    ("General Public", "aware of traditional council", ["O4"]),
    ("General Public", "where do people go for disputes", ["O4"]),
    ("General Public", "is it good women are leaders", ["O4"]),
    ("General Public", "support woman in family as leader", ["O4"]),
]


def normalize(text):
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def main():
    if not CLEANED_PATH.exists():
        sys.exit(
            f"Cannot find {CLEANED_PATH}.\n"
            "Run 02_clean_and_code_surveys.py first so the current question list is available."
        )

    data = pd.read_csv(CLEANED_PATH, dtype={"Question No": str})
    questions = (
        data[["respondent_group", "Question No", "Question"]]
        .drop_duplicates()
        .assign(key=lambda d: d["Question"].map(normalize))
    )

    rows, problems = [], []

    for group, phrase, codes in MAPPING_SPEC:
        pool = questions[questions["respondent_group"] == group]
        hits = pool[pool["key"].str.contains(re.escape(normalize(phrase)), regex=True)]

        if hits.empty:
            problems.append(f"NO MATCH   {group}: '{phrase}'")
            continue
        if len(hits) > 1:
            found = ", ".join(f"Q{q}" for q in hits["Question No"])
            problems.append(f"AMBIGUOUS  {group}: '{phrase}' matched {found}")
            continue

        question_no = hits["Question No"].iloc[0]
        for code in codes:
            objective, hypothesis = OBJECTIVES[code]
            rows.append({
                "respondent_group": group,
                "question_no": question_no,
                "objective": objective,
                "hypothesis": hypothesis,
            })

    mapping = pd.DataFrame(rows).drop_duplicates()
    mapping["_sort"] = pd.to_numeric(
        mapping["question_no"].str.extract(r"(\d+)")[0], errors="coerce"
    )
    mapping = mapping.sort_values(["objective", "respondent_group", "_sort"]).drop(columns="_sort")
    mapping.to_csv(OUTPUT_CSV, index=False)

    print(f"Wrote {len(mapping)} mapping rows to {OUTPUT_CSV}")
    print(f"Questions mapped: {mapping.groupby('respondent_group')['question_no'].nunique().to_dict()}")
    print("\nCoverage by objective:")
    print(mapping.groupby("objective")["question_no"].count().to_string())

    if problems:
        print(f"\n{len(problems)} PROBLEM(S) - these phrases need updating in MAPPING_SPEC:")
        for item in problems:
            print(f"  {item}")
        sys.exit(1)

    print("\nAll phrases resolved to exactly one question.")


if __name__ == "__main__":
    main()
