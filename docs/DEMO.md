# 85-second recording outline

Use the real application with the shareable Meridian synthetic corpus. No course
documents, real merchant data, mock model responses, or fabricated video are used.
The screenshots in `docs/demo/` are captures of the running local Streamlit app.
No video is supplied; the outline below is for your own recording.

## Launch

With dependencies installed and the existing Qwen 3.5 9B loaded in LM Studio:

```powershell
.\.venv\Scripts\python.exe demo.py
```

Open `http://127.0.0.1:8501`. The launcher copies only the synthetic PDF into an
ignored `.demo_runtime`, indexes it, and runs the existing Streamlit application.
It does not download a language model. If Qwen is not loaded:

```powershell
lms server start
lms load qwen/qwen3.5-9b --identifier coursenotes-qwen --context-length 8192
```

An existing embedding cache can be reused with `COURSENOTES_CACHE_DIR`. Otherwise
the first indexing run may need the configured E5 embedding download. The local
language model used for this evaluation was already present on disk.

## Recording sequence

| Time | Action and narration |
|---|---|
| 0–10 s | Show the synthetic-data banner. “CourseNotes answers English and French document questions locally. This is an original fictional operations corpus.” |
| 10–30 s | Ask: **What is the Atlas standard return window, and when does its refund arrive?** Show the real response and references. |
| 30–48 s | Ask: **Quel est le numérateur du taux de clic de campagne ?** Show the French response. |
| 48–63 s | Expand **Inspect retrieved source passages** if collapsed. Show the filename and physical page, and read the corresponding passage to check support yourself. |
| 63–78 s | Ask: **What is the personal email address of the Atlas returns manager?** Show the actual abstention; no contact data is supplied. |
| 78–85 s | “The evaluation uses 3 of 33 chunks and a separate held-out set. Citation validation checks coverage and page references; factual correctness and source support still need human review.” |

Leave room for actual inference latency; do not replace a failed response with a
manufactured one. If the model or server is unavailable, show the setup error and
use the saved screenshots only as clearly labeled historical captures.

## Screenshot verification

The optional `demo/capture_demo.mjs` uses Node's built-in Chrome DevTools client
and an already-installed Chrome/Chromium, with no npm packages or browser
downloads. It asks the three development questions above through the actual UI,
checks for live model/source output and abstention, and saves screenshots plus a
text receipt. It does not use held-out questions.

```powershell
.\.venv\Scripts\python.exe demo.py --port 8502
# In another terminal, with Node 22+ and an existing browser:
$env:CHROME_PATH = 'C:\path\to\chrome.exe'
node demo/capture_demo.mjs
```

See [English](demo/english.png), [French](demo/french.png),
[unsupported question](demo/unsupported.png), and [UI receipt](demo/ui_receipt.json).
