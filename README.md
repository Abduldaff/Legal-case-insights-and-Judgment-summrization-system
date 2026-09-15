# Legal Case Insights and Judgment Summarization System

A Streamlit application for extracting structured insights from legal judgments. Upload one judgment or analyze a portfolio of PDF judgments with evidence-grounded summaries, metadata extraction, disposition detection, visual analytics, and downloadable reports.

> **Important:** This application is an assistive document-analysis tool. It does not provide legal advice, determine the merits of a case, or replace review by a qualified legal professional. Always verify extracted facts against the source judgment.

## Features

### Single-case analysis

- Upload a judgment as a PDF or paste judgment text.
- Extract case title, case type, court, judge, and date when present.
- Generate a structured brief with background, legal issues, and judgment sections.
- Detect explicit disposition language such as allowed, dismissed, granted, upheld, or quashed.
- Show supporting evidence and an evidence-confidence score.
- Extract likely legal-issue statements for review.
- View the source text in the application.
- Download a plain-text analysis report.

### Bulk analyzer

The **Bulk analyzer** is a separate workspace page for multiple PDF judgments.

- Upload multiple PDFs in one operation.
- Analyze each case using the same model and extraction pipeline as single-case analysis.
- Filter results by disposition, case type, and minimum evidence confidence.
- View portfolio metrics for cases, pages, words, confidence, and issues.
- Explore visualizations for:
  - Disposition distribution
  - Case-type distribution
  - Confidence spread
  - Estimated reading workload
- Compare cases in a table.
- Export filtered portfolio results as CSV.
- Reuse cached results to avoid repeating unchanged analysis.

### Analysis modes

Select the mode from the sidebar:

| Mode | Behavior | Best for |
|---|---|---|
| **Fast** | Local extractive summarization; no transformer model loading | Quick review and large batches |
| **Balanced** | Lazy-loaded `sshleifer/distilbart-cnn-12-6` summarization | Better summaries with moderate resource use |
| **Detailed** | Lazy-loaded `facebook/bart-large-cnn` summarization | Higher-quality summaries when time and memory allow |

Fast mode is the default so the dashboard starts quickly. Transformer models are loaded only when Balanced or Detailed mode is selected.

## Project structure

```text
.
├── app.py             # Streamlit UI, dashboards, bulk analysis, charts, exports
├── summarizer.py      # Summarization, chunking, issue extraction, disposition detection
├── pdf_utils.py       # PDF text extraction with PyPDF2
├── case_metadata.py   # Court, judge, and date extraction
├── styles.css         # Dashboard styling and responsive layout
├── README.md
└── requirements.txt
```

## Requirements

- Python 3.9 or newer
- Streamlit
- PyPDF2
- Matplotlib
- Transformers, PyTorch, and their compatible dependencies for Balanced/Detailed modes

## Installation

Create and activate a virtual environment:

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install all project dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If you only need the default Fast mode, the lightweight dependencies are sufficient:

```powershell
python -m pip install streamlit PyPDF2 matplotlib
```

If the transformer stack is unavailable or incompatible, Fast mode remains available because the transformer import is deferred until a transformer mode is selected.

## Run the application

From the project directory:

```powershell
streamlit run app.py
```

Open the local URL shown by Streamlit, usually:

```text
http://localhost:8501
```

If that port is already in use, choose another one:

```powershell
streamlit run app.py --server.port 8503
```

## How to use

### Analyze one case

1. Open **Dashboard** or **Analyze case** from the sidebar.
2. Select **Upload PDF** or **Paste text**.
3. Choose an analysis mode.
4. Add the judgment.
5. Select **Analyze case**.
6. Review the case snapshot, identity, disposition evidence, legal issues, summary tabs, and source text.
7. Download the analysis report if required.

### Analyze multiple cases

1. Open **Bulk analyzer** from the sidebar.
2. Upload one or more PDF judgments.
3. Select **Analyze case portfolio**.
4. Use the filters to narrow the portfolio.
5. Review the charts and comparison table.
6. Select **Download portfolio CSV** to export the filtered results.

## How the analysis works

1. **PDF extraction:** `PyPDF2` extracts selectable text from each PDF.
2. **Text normalization:** Whitespace is normalized before analysis.
3. **Summarization:** Fast mode ranks representative legal sentences. Transformer modes summarize sentence-safe chunks.
4. **Metadata extraction:** Regular expressions search the judgment header for title, court, judge, and date information.
5. **Issue extraction:** Sentences containing legal issue markers such as `whether`, `issue`, `validity`, `liable`, and `jurisdiction` are surfaced.
6. **Disposition detection:** Explicit legal outcome phrases are matched and shown with nearby evidence.
7. **Caching:** Streamlit caches single-case and bulk analysis results so unchanged documents do not need to be processed again.

The disposition confidence score represents the strength of detected text evidence. It is **not** a probability that a party will win a case.

## Environment configuration

The transformer model can be changed without editing the source code:

### Windows PowerShell

```powershell
$env:LEGAL_SUMMARIZATION_MODEL = "your-huggingface-summarization-model"
streamlit run app.py
```

The environment variable is used by Balanced and Detailed modes. Fast mode does not load a transformer model.

## Supported document limitations

- PDFs must contain selectable text. Scanned image-only PDFs require OCR before upload.
- Metadata extraction depends on the judgment's formatting and wording.
- Case-type classification is keyword-based.
- Disposition detection only identifies explicit language that matches the configured patterns.
- Transformer models may require substantial RAM, disk space, and download time on first use.
- Long documents are summarized in chunks; always compare the generated brief with the original judgment.

## Troubleshooting

### The app starts slowly

Use **Fast** mode. Transformer models are downloaded and initialized only for Balanced or Detailed modes.

### The PDF produces little or no text

The PDF may be scanned or image-only. Run OCR first, then upload the searchable PDF.

### A transformer mode fails to load

Check that `transformers` and `torch` are installed in the same Python environment used to launch Streamlit. You can continue using Fast mode while resolving the transformer environment.

### Streamlit reports that a port is busy

Start the app on another port:

```powershell
streamlit run app.py --server.port 8503
```

## Privacy and data handling

The application processes uploaded documents in the running local Streamlit session. Do not upload confidential or privileged material to an environment unless that environment has been approved for the relevant data. Review your deployment, logging, and model-hosting configuration before using sensitive case documents.

## License

No license has been specified for this repository yet. Add a license file before distributing the project publicly.
