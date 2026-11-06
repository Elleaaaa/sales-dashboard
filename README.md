# Auto Analytics Dashboard

A browser-based, Power BI-inspired dashboard that automatically profiles uploaded datasets and creates interactive visualizations.

## Requirements
- Python 3.9+
- Packages listed in `requirements.txt`

## Run locally
1. Extract the ZIP file.
2. Open a terminal in the project folder.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL printed in the terminal (usually http://localhost:8501).

## Supported files
- Excel: `.xlsx`
- CSV: `.csv`
- Delimited text: `.txt` (tab, comma, semicolon, or pipe)

## Notes
- Date and numeric detection is heuristic; ambiguous columns may need manual correction in a future enhancement.
- TXT files should have a header row and a consistent delimiter.
- The app processes uploaded files in the running Python session. It does not permanently store uploads.
- This is a flexible starter application, not a full replacement for Power BI's data modelling, row-level security, or enterprise deployment features.
