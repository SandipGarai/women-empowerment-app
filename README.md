# Women Empowerment Survey Analysis

A Streamlit web application for analysing survey data on democratic decentralization and women empowerment among Oraon tribes in Mandar block, Ranchi district, Jharkhand.

## Live demo

This app is designed to run on [Streamlit Cloud](https://streamlit.io/cloud).

## How to run locally

1. Clone the repository.
2. Create a virtual environment and install dependencies:

```bash
python -m venv gui_env
# On Windows: gui_env\Scripts\activate
# On Linux/macOS: source gui_env/bin/activate
pip install -r requirements.txt
```

3. Launch the app:

```bash
streamlit run streamlit_app.py
```

4. Open `http://localhost:8501` in your browser and upload `Surveys.xlsx`.

## Running the analysis pipeline

You can run the full pipeline from the command line:

```bash
python 01_explore_surveys.py
python 02_clean_and_code_surveys.py
python 03_multi_response_coding.py
python 04_descriptive_results.py
python 05_restructure_matrix_questions.py
python 06_update_results_with_corrected_matrix.py
python 07_thematic_coding.py
python 08_merge_thematic_results.py
python 09_update_synopsis_mapping.py
python 10_validate_results.py
```

Or click **"Run Full Pipeline"** in the Streamlit app.

## Project structure

| File / folder | Purpose |
|---|---|
| `streamlit_app.py` | Main Streamlit GUI |
| `report_generator.py` | Word/PDF report generation |
| `create_pipeline_figure.py` | Pipeline diagram generator |
| `01_explore_surveys.py` … `10_validate_results.py` | Analysis pipeline scripts |
| `config/question_hypothesis_mapping.csv` | Editable question → objective/hypothesis mapping |
| `fonts/` | Bundled DejaVu fonts for PDF reports |
| `requirements.txt` | Python dependencies |

## Outputs

The `outputs/` folder is created automatically when you run the pipeline. It contains:

- `exploration/` — workbook overview and response frequencies
- `cleaned/` — cleaned long/wide responses
- `multi_response/` — multi-response coding
- `descriptive_results/` — frequency tables, question summary, table index
- `matrix_corrected/` — restructured matrix questions
- `thematic_coding/` — thematic coding results and review workbook
- `synopsis_mapping/` — findings by synopsis objective
- `validation/` — validation checks and action list

## Customizing the mapping

Edit `config/question_hypothesis_mapping.csv` directly, or use the **🎯 Question Mapping** tab in the Streamlit app.

## Data input

The app expects an Excel file named `Surveys.xlsx` with the following sheets:

- Women Representative
- Govt Officials
- Mahila Mukhiya
- Traditional Leader
- General Public
