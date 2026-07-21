#!/bin/bash
# Launch the Women Empowerment Survey Analysis GUI
# Usage: ./run_gui.sh
# Then open http://localhost:8501 in your browser.

cd "$(dirname "$0")"

if [ ! -d "gui_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv gui_env
fi

echo "Installing required packages (if needed)..."
gui_env/bin/pip install -q streamlit pandas openpyxl plotly python-docx fpdf2

echo "Starting GUI..."
gui_env/bin/streamlit run streamlit_app.py \
    --server.headless true \
    --server.port 8501 \
    --browser.gatherUsageStats false
