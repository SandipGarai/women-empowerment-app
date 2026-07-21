# Women Empowerment Survey Analysis — GUI Guide

This folder now contains a **browser-based GUI** for the entire survey analysis pipeline. You do not need to write or edit Python code to use it.

---

## What the GUI can do

1. **Upload** your `Surveys.xlsx` file.
2. **Run** the full analysis pipeline with one click.
3. **Automatically restructure** matrix questions (Women Representative Q19, Q21, Q23) into sub-items.
4. **Map** each survey question to the correct synopsis objective and hypothesis.
5. **View** descriptive results by theme.
6. **Create** interactive bar charts and pie charts.
7. **Check** validation and quality issues.
8. **Download** a Word or PDF report.

---

## How to start the GUI

### On Linux / this computer

Open a terminal in the `Women_empowerment` folder and run:

```bash
./run_gui.sh
```

Then open your browser and go to:

```
http://localhost:8501
```

### First-time setup (if `run_gui.sh` does not work)

```bash
cd /data/sandip/Women_empowerment
python3 -m venv gui_env
gui_env/bin/pip install -r requirements_gui.txt
gui_env/bin/streamlit run streamlit_app.py
```

---

## Step-by-step workflow

### Step 1 — Upload data
- In the left sidebar, click **Browse files** under "Upload Data".
- Select your `Surveys.xlsx` file.
- The file will be saved as `Surveys.xlsx` in this folder.
  - Your original file is automatically backed up as `Surveys_original_backup.xlsx`.

### Step 2 — Run the pipeline
- Click the **🚀 Run Full Pipeline** button in the sidebar.
- Wait until you see the green "Pipeline completed successfully!" message.

### Step 3 — Map questions to objectives
- Go to the **🎯 Question Mapping** tab.
- For each question, choose the correct **Objective** and **Hypothesis** from the dropdowns.
- Click **💾 Save Mapping**.

### Step 4 — Explore results
- **📈 Results** tab: view tables by theme.
- **📊 Visualizations** tab: create bar charts and pie charts.
- **✅ Validation** tab: check for issues like matrix questions or missing data.

### Step 5 — Generate report
- In the sidebar, enter a report title and author name.
- Click **📄 Word Report** or **📕 PDF Report**.
- A download button will appear. Click it to save your report.

---

## Tabs explained

| Tab | Purpose |
|---|---|
| 🏠 Home | Overview of respondent groups and synopsis objectives |
| 📋 Data Preview | View the raw Excel data sheet by sheet |
| 🎯 Question Mapping | Link each question to an objective/hypothesis |
| 📈 Results | Final descriptive tables by theme |
| 📊 Visualizations | Interactive charts for selected questions |
| ✅ Validation | Quality checks and action items |
| 📖 How to Use | In-app help |

---

## Important notes

- **Matrix questions:** Women Representative Q19, Q21, and Q23 are automatically restructured into sub-items (e.g., 19.1, 19.2, 19.3, 19.4) during the pipeline run. You can view the corrected scale statistics in `outputs/matrix_corrected/`.
- **Missing data:** Blank or "don't know" answers are labeled **"Not mentioned/Do not know"**. This is a valid response category.
- **Multi-response questions:** Percentages can add up to more than 100% because respondents can select multiple answers.
- **Reports:** Word reports include detailed tables if "Include detailed tables" is checked. PDF reports are shorter and focus on findings by objective.

---

## Files created by the GUI

| File | Purpose |
|---|---|
| `streamlit_app.py` | Main GUI application |
| `report_generator.py` | Generates Word and PDF reports |
| `run_gui.sh` | One-click launcher |
| `requirements_gui.txt` | Python packages needed |
| `gui_env/` | Virtual environment (created automatically) |
| `Surveys_original_backup.xlsx` | Backup of original data file |
| `outputs/gui_report.docx` | Generated Word report |
| `outputs/gui_report.pdf` | Generated PDF report |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Port 8501 already in use | Edit `run_gui.sh` and change `--server.port 8501` to another port, e.g., `8502` |
| App does not load | Check that `gui_env` was created and packages installed. Re-run `./run_gui.sh`. |
| Pipeline fails | Go to the Validation tab and check the error message. Usually caused by a changed Excel structure. |
| PDF report looks wrong | The PDF is a simple summary. For full tables, use the Word report. |

---

## Next improvements you may want

1. Add automatic restructuring of matrix questions (Q19, Q21, Q23).
2. Add thematic coding interface for open-ended questions.
3. Add cross-tabulations (e.g., by gender or age group).
4. Add more chart types (stacked bars, line charts, word clouds).
