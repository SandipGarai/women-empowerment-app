"""
Women Empowerment Survey Analysis GUI
======================================
A browser-based application to:
  1. Upload the Surveys.xlsx file
  2. Run the full analysis pipeline
  3. Map questions to synopsis objectives/hypotheses
  4. View results, create charts
  5. Download Word or PDF reports

How to run:
    cd /data/sandip/Women_empowerment
    gui_env/bin/streamlit run streamlit_app.py

Then open the URL shown in the terminal (usually http://localhost:8501).
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from report_generator import generate_pdf_report, generate_word_report


# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = PROJECT_DIR / "outputs"
MAPPING_DIR = OUTPUTS_DIR / "synopsis_mapping"
MAPPING_FILE = MAPPING_DIR / "objectives_with_top_findings.xlsx"
DEFAULT_EXCEL = PROJECT_DIR / "Surveys.xlsx"

OBJECTIVES = [
    "Obj 1: 73rd Amendment impact on representation & participation",
    "Obj 2: Effectiveness of capacity building initiatives",
    "Obj 3: Role of ICT in promoting participation",
    "Obj 4: Participation → empowerment & community development",
    "Not mapped",
]

HYPOTHESES = [
    "H1: 73rd Amendment increased representation/participation → empowerment",
    "H2: Capacity building enhances participation & empowerment",
    "H3: ICT played a crucial role",
    "H4: Participation contributed to empowerment & community development",
    "Not mapped",
]

THEMES = [
    "Respondent Profile",
    "General Public: Awareness and Access",
    "Women Empowerment and Panchayat Participation",
    "Challenges and Constraints",
    "Traditional vs Formal Governance",
    "ICT and Digital Access",
    "Agriculture and Livelihood",
    "Government Officials Perspective",
    "Mahila Mukhiya Perspective",
    "Traditional Leader Perspective",
    "Women Representative Perspective",
    "Other",
]


def safe_text(value):
    """Convert any value to a displayable string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------
def run_analysis_pipeline():
    """Run the five analysis scripts in order using the virtual environment Python."""
    scripts = [
        "01_explore_surveys.py",
        "02_clean_and_code_surveys.py",
        "03_multi_response_coding.py",
        "04_descriptive_results.py",
        "05_restructure_matrix_questions.py",
        "06_update_results_with_corrected_matrix.py",
        "07_thematic_coding.py",
        "08_merge_thematic_results.py",
        "09_update_synopsis_mapping.py",
        "10_validate_results.py",  # Run validation last, after all corrections/coding
    ]
    progress = st.progress(0, text="Starting analysis pipeline...")
    # Use the correct virtual-environment Python path for the OS
    if sys.platform.startswith("win"):
        python = PROJECT_DIR / "gui_env" / "Scripts" / "python.exe"
    else:
        python = PROJECT_DIR / "gui_env" / "bin" / "python"
    if not python.exists():
        python = sys.executable

    for i, script in enumerate(scripts):
        progress.progress(
            int((i / len(scripts)) * 100),
            text=f"Running {script}...",
        )
        result = subprocess.run(
            [str(python), str(PROJECT_DIR / script)],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            progress.empty()
            st.error(f"Error running {script}:\n\n{result.stderr}")
            return False

    # Re-create the synopsis mapping after pipeline run
    recreate_synopsis_mapping()
    progress.progress(100, text="Analysis complete!")
    progress.empty()
    return True


def recreate_synopsis_mapping():
    """Recreate the objectives_with_top_findings file after a pipeline run."""
    q_summary_path = OUTPUTS_DIR / "descriptive_results" / "question_level_summary.csv"
    if not q_summary_path.exists():
        return

    q_summary = pd.read_csv(q_summary_path)

    # Load editable mapping from config CSV; fall back to default if missing.
    config_dir = PROJECT_DIR / "config"
    mapping_csv = config_dir / "question_hypothesis_mapping.csv"
    if mapping_csv.exists():
        mapping_df = pd.read_csv(mapping_csv)
        mapping_df["question_no"] = mapping_df["question_no"].astype(str)
    else:
        # The mapping lives in config/question_hypothesis_mapping.csv so it can
        # be edited without touching code. A stale copy hard-coded here caused
        # silent mismatches whenever the workbook was renumbered, so there is
        # no in-code fallback any more.
        st.error(
            "Missing config/question_hypothesis_mapping.csv. "
            "This file maps each survey question to a synopsis objective and "
            "hypothesis. Restore it, then reload."
        )
        return

    # Matrix sub-items now carry their own question numbers in the workbook
    # (involvement = Q19-Q22, challenges = Q24-Q31, change-since = Q33-Q36),
    # so no expansion step is needed; they are mapped directly in the config CSV.
    def as_question_key(value):
        if pd.isna(value):
            return ""
        text = str(value).strip()
        return text[:-2] if text.endswith(".0") else text

    mapping_df["question_no"] = mapping_df["question_no"].map(as_question_key)

    # Prefer thematic coding rows where available (they are the primary result
    # for open-ended questions). Sort so "thematic" comes first, then drop
    # duplicates by respondent_group + question_no.
    q_summary = q_summary.sort_values(
        "result_type",
        key=lambda col: col.eq("thematic").astype(int),
        ascending=False,
    )
    q_summary = q_summary.drop_duplicates(
        subset=["respondent_group", "question_no"],
        keep="first",
    )

    # Merge with question summary to get top findings
    q_summary["question_no_str"] = q_summary["question_no"].apply(
        lambda x: str(int(x)) if pd.notna(x) and x == int(x) else str(x)
    )
    # Drop the original numeric question_no to avoid column name collisions
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
    # Provide default empty strings for missing columns
    merged["finding_type"] = merged["finding_type"].fillna("Mapped question")
    merged["question"] = merged.get("question", "")
    merged["top_answer"] = merged.get("top_answer", "")
    merged["top_count"] = merged.get("top_count", "")
    merged["denominator_n"] = merged.get("denominator_n", "")
    merged["top_percent"] = merged.get("top_percent", "")

    merged = merged[final_cols]
    MAPPING_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_excel(MAPPING_FILE, index=False)


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
@st.cache_data
def load_workbook_overview():
    path = OUTPUTS_DIR / "exploration" / "workbook_overview.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_all_results():
    path = OUTPUTS_DIR / "descriptive_results" / "all_descriptive_results.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_question_summary():
    path = OUTPUTS_DIR / "descriptive_results" / "question_level_summary.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_validation_status():
    path = OUTPUTS_DIR / "validation" / "validation_status_summary.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_validation_actions():
    path = OUTPUTS_DIR / "validation" / "validation_action_list.csv"
    return pd.read_csv(path) if path.exists() else None


@st.cache_data
def load_mapping():
    if MAPPING_FILE.exists():
        return pd.read_excel(MAPPING_FILE)
    return pd.DataFrame(
        columns=[
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
    )


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------
def create_bar_chart(df, x_col, y_col, color_col=None, title="", orientation="v"):
    """Create an interactive Plotly bar chart."""
    if df is None or df.empty:
        return None
    plot_df = df.copy()
    if orientation == "h":
        fig = px.bar(
            plot_df,
            y=x_col,
            x=y_col,
            color=color_col,
            title=title,
            orientation="h",
        )
    else:
        fig = px.bar(
            plot_df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=title,
        )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Percent/Count",
        title_x=0.5,
        height=500,
    )
    return fig


def create_pie_chart(df, names_col, values_col, title=""):
    """Create an interactive Plotly pie chart."""
    if df is None or df.empty:
        return None
    fig = px.pie(df, names=names_col, values=values_col, title=title)
    fig.update_layout(title_x=0.5, height=500)
    return fig


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Women Empowerment Survey Analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📊 Women Empowerment Survey Analysis")
    st.markdown(
        "Upload your `Surveys.xlsx` file, run the analysis pipeline, map questions to your "
        "synopsis objectives, and download reports."
    )

    # -----------------------------------------------------------------------
    # Sidebar
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.header("1. Upload Data")
        uploaded_file = st.file_uploader("Upload Surveys.xlsx", type=["xlsx"])

        if uploaded_file is not None:
            # Backup existing file if it is not the same as the uploaded one
            if DEFAULT_EXCEL.exists():
                backup_path = PROJECT_DIR / "Surveys_original_backup.xlsx"
                import shutil
                shutil.copy2(DEFAULT_EXCEL, backup_path)
            save_path = DEFAULT_EXCEL
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Saved as {save_path.name}. Original backed up to Surveys_original_backup.xlsx")
        else:
            save_path = DEFAULT_EXCEL if DEFAULT_EXCEL.exists() else None

        st.divider()
        st.header("2. Run Analysis")
        if st.button("🚀 Run Full Pipeline", use_container_width=True):
            with st.spinner("Running analysis... please wait"):
                if run_analysis_pipeline():
                    st.success("Pipeline completed successfully!")
                    st.cache_data.clear()
                else:
                    st.error("Pipeline failed. Check error message above.")

        st.divider()
        st.header("3. Generate Report")
        report_title = st.text_input("Report title", value="Women Empowerment Analysis Report")
        report_author = st.text_input("Author name (optional)")
        include_tables = st.checkbox("Include detailed tables", value=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Word Report", use_container_width=True):
                if not MAPPING_FILE.exists():
                    st.error("Please run the pipeline first.")
                else:
                    out_path = OUTPUTS_DIR / "gui_report.docx"
                    generate_word_report(
                        out_path,
                        title=report_title,
                        author=report_author,
                        objective_mapping_path=MAPPING_FILE,
                        all_results_path=OUTPUTS_DIR / "descriptive_results" / "all_descriptive_results.csv",
                        question_summary_path=OUTPUTS_DIR / "descriptive_results" / "question_level_summary.csv",
                        validation_status_path=OUTPUTS_DIR / "validation" / "validation_status_summary.csv",
                        include_tables=include_tables,
                    )
                    with open(out_path, "rb") as f:
                        st.download_button(
                            label="Download Word",
                            data=f,
                            file_name="Women_Empowerment_Report.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
        with col2:
            if st.button("📕 PDF Report", use_container_width=True):
                if not MAPPING_FILE.exists():
                    st.error("Please run the pipeline first.")
                else:
                    out_path = OUTPUTS_DIR / "gui_report.pdf"
                    generate_pdf_report(
                        out_path,
                        title=report_title,
                        objective_mapping_path=MAPPING_FILE,
                    )
                    with open(out_path, "rb") as f:
                        st.download_button(
                            label="Download PDF",
                            data=f,
                            file_name="Women_Empowerment_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )

        st.divider()
        st.info(
            "💡 **Tip:** If you change the question mapping in the app, click "
            "'Save Mapping' before generating the report."
        )

    # -----------------------------------------------------------------------
    # Tabs
    # -----------------------------------------------------------------------
    tabs = st.tabs(
        ["🏠 Home", "📋 Data Preview", "🎯 Question Mapping", "📈 Results", "📊 Visualizations", "✅ Validation", "📖 How to Use"]
    )

    # ---- Home tab ----
    with tabs[0]:
        st.header("Project Overview")
        col1, col2, col3 = st.columns(3)
        overview = load_workbook_overview()
        if overview is not None:
            col1.metric("Respondent Groups", overview["sheet"].nunique())
            col2.metric("Total Respondents", overview["respondent_columns"].sum())
            col3.metric("Total Question Rows", overview["question_rows"].sum())

            st.subheader("Sheet Overview")
            st.dataframe(overview, use_container_width=True)
        else:
            st.warning("No outputs found. Please upload data and run the pipeline.")

        st.subheader("Synopsis Objectives & Hypotheses")
        obj_data = {
            "Objective": [
                "Obj 1: 73rd Amendment impact on representation & participation",
                "Obj 2: Effectiveness of capacity building initiatives",
                "Obj 3: Role of ICT in promoting participation",
                "Obj 4: Participation → empowerment & community development",
            ],
            "Hypothesis": [
                "H1: 73rd Amendment increased representation/participation → empowerment",
                "H2: Capacity building enhances participation & empowerment",
                "H3: ICT played a crucial role",
                "H4: Participation contributed to empowerment & community development",
            ],
        }
        st.dataframe(pd.DataFrame(obj_data), use_container_width=True)

    # ---- Data Preview tab ----
    with tabs[1]:
        st.header("Raw Data Preview")
        if save_path and Path(save_path).exists():
            try:
                xls = pd.ExcelFile(save_path)
                sheet = st.selectbox("Select sheet", xls.sheet_names)
                df_preview = pd.read_excel(save_path, sheet_name=sheet)
                st.write(f"Rows: {len(df_preview)}, Columns: {len(df_preview.columns)}")
                st.dataframe(df_preview.head(20), use_container_width=True)
            except Exception as e:
                st.error(f"Could not read file: {e}")
        else:
            st.warning("No data file available. Please upload Surveys.xlsx.")

    # ---- Question Mapping tab ----
    with tabs[2]:
        st.header("Map Questions to Objectives & Hypotheses")
        st.markdown(
            "Here you can decide which question belongs to which synopsis objective and hypothesis. "
            "You can also assign a theme. Changes are saved to a file and used in the report."
        )

        mapping_df = load_mapping()
        q_summary = load_question_summary()

        if mapping_df.empty and q_summary is not None:
            # Build a default editable mapping from question summary
            q_summary["objective"] = "Not mapped"
            q_summary["hypothesis"] = "Not mapped"
            mapping_df = q_summary.rename(
                columns={
                    "respondent_group": "respondent_group",
                    "question_no": "question_no",
                    "question": "question",
                    "top_answer": "top_answer",
                    "top_count": "top_count",
                    "denominator_n": "denominator_n",
                    "top_percent": "top_percent",
                }
            )
            mapping_df["finding_type"] = "Mapped question"
            mapping_df = mapping_df[
                [
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
            ]

        if not mapping_df.empty:
            edited_mapping = st.data_editor(
                mapping_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "objective": st.column_config.SelectboxColumn(
                        "Objective", options=OBJECTIVES, required=False
                    ),
                    "hypothesis": st.column_config.SelectboxColumn(
                        "Hypothesis", options=HYPOTHESES, required=False
                    ),
                    "respondent_group": st.column_config.TextColumn("Group", disabled=True),
                    "question_no": st.column_config.TextColumn("Q No", disabled=True),
                    "question": st.column_config.TextColumn("Question", disabled=True, width="large"),
                    "top_answer": st.column_config.TextColumn("Top Answer", disabled=True),
                    "top_percent": st.column_config.NumberColumn("Top %", disabled=True),
                },
                hide_index=True,
            )

            if st.button("💾 Save Mapping", use_container_width=True):
                MAPPING_DIR.mkdir(parents=True, exist_ok=True)
                edited_mapping.to_excel(MAPPING_FILE, index=False)
                # Also persist the core mapping to CSV so pipeline re-runs keep edits
                config_dir = PROJECT_DIR / "config"
                config_dir.mkdir(parents=True, exist_ok=True)
                core_cols = ["respondent_group", "question_no", "objective", "hypothesis"]
                csv_cols = [c for c in core_cols if c in edited_mapping.columns]
                edited_mapping[csv_cols].to_csv(
                    config_dir / "question_hypothesis_mapping.csv", index=False
                )
                st.success(f"Mapping saved to {MAPPING_FILE} and config/question_hypothesis_mapping.csv")
                st.cache_data.clear()

            # Filter view by objective
            st.subheader("View by Objective")
            selected_objective = st.selectbox("Select objective", ["All"] + OBJECTIVES)
            if selected_objective != "All":
                st.dataframe(
                    edited_mapping[edited_mapping["objective"] == selected_objective],
                    use_container_width=True,
                    hide_index=True,
                )
        else:
            st.warning("No mapping data. Please run the pipeline first.")

    # ---- Results tab ----
    with tabs[3]:
        st.header("Descriptive Results by Theme")
        results_df = load_all_results()

        if results_df is not None:
            theme = st.selectbox("Select theme", sorted(results_df["theme"].unique()))
            group_filter = st.multiselect(
                "Filter respondent group",
                options=sorted(results_df["respondent_group"].unique()),
                default=sorted(results_df["respondent_group"].unique()),
            )

            filtered = results_df[
                (results_df["theme"] == theme)
                & (results_df["respondent_group"].isin(group_filter))
            ].copy()

            st.write(f"Showing {len(filtered)} rows")
            st.dataframe(
                filtered[
                    [
                        "respondent_group",
                        "question_no",
                        "question",
                        "answer",
                        "count",
                        "denominator_n",
                        "percent_of_respondents",
                        "result_type",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            csv = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download filtered results as CSV",
                data=csv,
                file_name=f"results_{theme.replace(' ', '_')}.csv",
                mime="text/csv",
            )
        else:
            st.warning("No results found. Please run the pipeline first.")

    # ---- Visualizations tab ----
    with tabs[4]:
        st.header("Visualizations")
        results_df = load_all_results()

        if results_df is not None:
            col1, col2 = st.columns(2)
            with col1:
                viz_theme = st.selectbox("Select theme", sorted(results_df["theme"].unique()), key="viz_theme")
            with col2:
                viz_group = st.selectbox(
                    "Select respondent group",
                    ["All"] + sorted(results_df["respondent_group"].unique()),
                    key="viz_group",
                )

            plot_data = results_df[results_df["theme"] == viz_theme].copy()
            if viz_group != "All":
                plot_data = plot_data[plot_data["respondent_group"] == viz_group]

            # Get top questions in this theme
            top_questions = (
                plot_data.groupby(["question_no", "question"])
                .size()
                .reset_index(name="rows")
                .sort_values("rows", ascending=False)
                .head(10)
            )

            if not top_questions.empty:
                selected_question = st.selectbox(
                    "Select question to visualize",
                    options=top_questions.apply(
                        lambda r: f"Q{r['question_no']}: {r['question'][:80]}", axis=1
                    ).tolist(),
                )
                q_no = selected_question.split(":")[0].replace("Q", "").strip()
                chart_df = plot_data[plot_data["question_no"].astype(str) == q_no].copy()
                chart_df = chart_df.sort_values("percent_of_respondents", ascending=False).head(15)

                chart_type = st.radio("Chart type", ["Bar chart", "Horizontal bar", "Pie chart"], horizontal=True)

                if chart_type == "Bar chart":
                    fig = create_bar_chart(
                        chart_df,
                        x_col="answer",
                        y_col="percent_of_respondents",
                        title=f"{selected_question[:80]}",
                    )
                elif chart_type == "Horizontal bar":
                    fig = create_bar_chart(
                        chart_df,
                        x_col="answer",
                        y_col="percent_of_respondents",
                        title=f"{selected_question[:80]}",
                        orientation="h",
                    )
                else:
                    fig = create_pie_chart(
                        chart_df,
                        names_col="answer",
                        values_col="count",
                        title=f"{selected_question[:80]}",
                    )

                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Not enough data for chart.")
            else:
                st.warning("No questions found for selected theme/group.")
        else:
            st.warning("No results found. Please run the pipeline first.")

    # ---- Validation tab ----
    with tabs[5]:
        st.header("Validation & Quality Checks")
        status_df = load_validation_status()
        actions_df = load_validation_actions()

        if status_df is not None:
            st.subheader("Overall Status")
            # Color-code status
            def color_status(val):
                if val == "PASS":
                    return "background-color: #d4edda; color: #155724"
                elif val == "FAIL":
                    return "background-color: #f8d7da; color: #721c24"
                else:
                    return "background-color: #fff3cd; color: #856404"

            st.dataframe(
                status_df.style.map(color_status, subset=["status"]),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.warning("No validation status found. Please run the pipeline first.")

        if actions_df is not None:
            st.subheader("Detailed Action List")
            severity_filter = st.multiselect(
                "Filter by severity",
                options=sorted(actions_df["severity"].unique()),
                default=sorted(actions_df["severity"].unique()),
            )
            issue_filter = st.multiselect(
                "Filter by issue type",
                options=sorted(actions_df["issue_type"].unique()),
                default=sorted(actions_df["issue_type"].unique()),
            )
            filtered_actions = actions_df[
                (actions_df["severity"].isin(severity_filter))
                & (actions_df["issue_type"].isin(issue_filter))
            ]
            st.dataframe(filtered_actions, use_container_width=True, hide_index=True)
        else:
            st.warning("No validation actions found.")

    # ---- How to Use tab ----
    with tabs[6]:
        st.header("How to Use This App")
        st.markdown(
            """
            ### Step-by-step guide

            1. **Upload your data** in the sidebar (or use the existing `Surveys.xlsx`).
            2. Click **Run Full Pipeline**. This executes all five analysis scripts.
            3. Go to **Question Mapping** and assign each question to the correct objective/hypothesis.
               - Click **Save Mapping** when done.
            4. Explore **Results by Theme** and **Visualizations**.
            5. Check the **Validation** tab for any issues that need your attention.
            6. Click **Word Report** or **PDF Report** in the sidebar to download your report.

            ### Important notes

            - **Matrix questions** (involvement Q19-Q22, challenges Q24-Q31, change-since Q33-Q36) are currently flagged
              because they contain several sub-questions. You may need to restructure them
              before finalizing the report.
            - **"Not mentioned/Do not know"** is a valid response category. It means the
              respondent did not answer or did not know.
            - **Multi-response questions** can have percentages that add up to more than 100%
              because one respondent can select multiple answers.

            ### Output folders

            All generated files are saved in the `outputs/` folder:
            - `descriptive_results/` — final tables
            - `validation/` — quality checks
            - `synopsis_mapping/` — question-to-objective mapping
            """
        )


if __name__ == "__main__":
    main()
