"""
Create a pipeline flowchart figure for the Women Empowerment analysis.
Run this script to generate pipeline_figure.png / pipeline_figure.pdf.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "pipeline_figure.png"
PDF_PATH = PROJECT_DIR / "pipeline_figure.pdf"

# Define pipeline stages: (script, short title, description, outputs, color)
STAGES = [
    (
        "Input",
        "Raw Data",
        "Surveys.xlsx (5 sheets)\nSynopsis V6 PDF",
        "",
        "#E8E8E8",
    ),
    (
        "01_explore_surveys.py",
        "Explore",
        "Reads Excel sheets, identifies\nsections and respondent counts",
        "outputs/exploration/\nworkbook_overview.csv",
        "#AED6F1",
    ),
    (
        "02_clean_and_code_surveys.py",
        "Clean & Code",
        "Normalises text; codes\nyes/no, gender, age,\ncommunity, missing values",
        "outputs/cleaned/\ncleaned_analysis_responses.csv",
        "#A9DFBF",
    ),
    (
        "03_multi_response_coding.py",
        "Multi-Response",
        "Splits comma-separated\nanswers (crops, info channels,\nlivestock, techniques)",
        "outputs/multi_response/\nmulti_response_summary.csv",
        "#A9DFBF",
    ),
    (
        "04_descriptive_results.py",
        "Descriptive Stats",
        "Frequency tables, percentages,\nassigns thesis themes",
        "outputs/descriptive_results/\nall_descriptive_results.csv",
        "#F9E79F",
    ),
    (
        "05_restructure_matrix_questions.py",
        "Restructure Matrix",
        "Extracts sub-items for Women\nRep Q19, Q21, Q23 (scale /\ncategorical responses)",
        "outputs/matrix_corrected/\ncorrected_matrix_frequencies.csv",
        "#F9E79F",
    ),
    (
        "06_update_results_with_corrected_matrix.py",
        "Merge Matrix",
        "Replaces old matrix rows with\ncorrected sub-items in final results",
        "Updated descriptive\nresults & summaries",
        "#F9E79F",
    ),
    (
        "07_thematic_coding.py",
        "Thematic Coding",
        "Codes 16 key open-ended\nquestions into themes using\nkeyword-based rules",
        "outputs/thematic_coding/\nthematic_frequencies.csv\nthematic_coding_review.xlsx",
        "#F5B7B1",
    ),
    (
        "08_merge_thematic_results.py",
        "Merge Thematic",
        "Adds thematic rows to final\nresults; old rows kept as\nraw_open_ended",
        "Updated results with\nthematic tables",
        "#F5B7B1",
    ),
    (
        "09_update_synopsis_mapping.py",
        "Synopsis Mapping",
        "Maps questions to 4 objectives /\nhypotheses; updates top findings",
        "outputs/synopsis_mapping/\nobjectives_with_top_findings.xlsx\nTOP_FINDINGS_BY_OBJECTIVE.md",
        "#D7BDE2",
    ),
    (
        "10_validate_results.py",
        "Validate",
        "Checks respondent counts, missing\ndominance, fragmentation, themes,\ncount logic",
        "outputs/validation/\nvalidation_status_summary.csv\nresult_tables_for_manual_review.xlsx",
        "#F1948A",
    ),
    (
        "streamlit_app.py\nreport_generator.py",
        "GUI & Reports",
        "Interactive browser app,\nWord / PDF reports, visualisations",
        "gui_report_test.docx\ngui_report_test.pdf\nhttp://localhost:8501",
        "#BB8FCE",
    ),
]


def draw_pipeline():
    fig, ax = plt.subplots(figsize=(18, 26))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 26)
    ax.axis("off")

    # Title
    ax.text(
        9, 25.3,
        "Women Empowerment Survey Analysis Pipeline",
        ha="center", va="center",
        fontsize=24, weight="bold",
    )
    ax.text(
        9, 24.8,
        "What each script does and how outputs flow",
        ha="center", va="center",
        fontsize=13, style="italic", color="#555555",
    )

    # Layout parameters
    box_width = 7.0
    box_height = 1.55
    x_left = 1.0
    x_right = 10.0
    y_start = 23.0
    y_step = 1.95

    for i, (script, title, desc, outputs, color) in enumerate(STAGES):
        # Alternate left/right for readability
        x = x_left if i % 2 == 0 else x_right
        y = y_start - i * y_step

        # Draw main box
        box = FancyBboxPatch(
            (x, y - box_height / 2),
            box_width, box_height,
            boxstyle="round,pad=0.05,rounding_size=0.18",
            facecolor=color,
            edgecolor="#333333",
            linewidth=1.5,
        )
        ax.add_patch(box)

        # Script name (top, bold, monospace)
        ax.text(
            x + box_width / 2, y + box_height / 2 - 0.20,
            script,
            ha="center", va="top",
            fontsize=10, weight="bold", family="monospace",
        )

        # Title (middle)
        ax.text(
            x + box_width / 2, y + 0.08,
            title,
            ha="center", va="center",
            fontsize=13, weight="bold",
        )

        # Description (below title)
        ax.text(
            x + box_width / 2, y - 0.22,
            desc,
            ha="center", va="top",
            fontsize=9, linespacing=1.15,
        )

        # Outputs box (smaller, below main box)
        if outputs:
            out_y = y - box_height / 2 - 0.50
            out_box = FancyBboxPatch(
                (x + 0.4, out_y - 0.48),
                box_width - 0.8, 0.60,
                boxstyle="round,pad=0.02,rounding_size=0.08",
                facecolor="#FFFFFF",
                edgecolor="#666666",
                linewidth=1,
                linestyle="--",
            )
            ax.add_patch(out_box)
            ax.text(
                x + box_width / 2, out_y - 0.18,
                f"Outputs:\n{outputs}",
                ha="center", va="center",
                fontsize=8, color="#444444", linespacing=1.1,
            )

        # Draw arrow to next stage
        if i < len(STAGES) - 1:
            next_x = x_right if (i + 1) % 2 == 0 else x_left
            next_y = y_start - (i + 1) * y_step

            if x == x_left:
                start = (x + box_width, y)
                end = (next_x, next_y)
            else:
                start = (x, y)
                end = (next_x + box_width, next_y)

            arrow = FancyArrowPatch(
                start, end,
                arrowstyle="-|>",
                color="#555555",
                linewidth=1.8,
                mutation_scale=14,
                connectionstyle="arc3,rad=0.12",
            )
            ax.add_patch(arrow)

    # Notes box at bottom (single column, clear)
    note_text = (
        "Notes:\n"
        "• 01-04: Produce the core cleaned data and frequency tables.\n"
        "• 05-06: Fix Women Representative matrix questions (Q19, Q21, Q23).\n"
        "• 07-08: Add thematic coding for 16 important open-ended questions.\n"
        "• 09: Map all results to the four synopsis objectives/hypotheses.\n"
        "• 10: Runs last to validate everything.\n"
        "• Launch GUI: ./run_gui.sh  →  http://localhost:8501"
    )
    ax.text(
        9, 1.5,
        note_text,
        ha="center", va="center",
        fontsize=10.5,
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#F8F9F9", edgecolor="#AAB7B8"),
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight", facecolor="white")
    plt.savefig(PDF_PATH, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved pipeline figure:\n  {OUTPUT_PATH}\n  {PDF_PATH}")


if __name__ == "__main__":
    draw_pipeline()
