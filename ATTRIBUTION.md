# Attribution and license scope

## Repository source and fixtures

The available Git history starts at `32ceba2`, a portfolio import of an existing application, and records later retrieval, validation, evaluation, and demo changes. Source headers and the available history do not identify a copied upstream application or carry a third-party application notice. This inspection does not establish the pre-import origin of `core.py` and `app.py`; no earlier source history or upstream permission record is included. Confirm whether those imported files contain adapted third-party snippets and, if so, identify their sources and applicable notices before selecting a project-wide license. Git authorship alone does not resolve that question.

The Meridian handbook, synthetic questions, and reference answers were authored by the coding assistant for this project, as recorded in [VALIDATION.md](VALIDATION.md) and [evaluation/README.md](evaluation/README.md). They describe fictional policies. Demo images are actual local UI captures using that corpus; the [receipt](docs/demo/ui_receipt.json) records their source. No real course PDFs or merchant data are distributed.

## Third-party components

These are imported dependencies or external model/runtime resources, not claims of project authorship. The pinned package versions are in `requirements.txt`; the historical environment snapshot is in `requirements-lock.txt`. Upstream license files and package notices remain applicable to their components.

| Component | Use and upstream source |
| --- | --- |
| Streamlit | Interface; [upstream](https://github.com/streamlit/streamlit) |
| LangChain | PDF loader, splitting, vectors, prompts; [license](https://github.com/langchain-ai/langchain/blob/master/LICENSE) |
| LangGraph | Bounded workflow; [upstream](https://github.com/langchain-ai/langgraph) |
| Sentence Transformers | Embedding runtime; [upstream](https://github.com/huggingface/sentence-transformers) |
| PyPDF | PDF extraction; [upstream](https://github.com/py-pdf/pypdf) |
| NumPy | Numerical operations; [upstream](https://github.com/numpy/numpy) |
| ReportLab | Synthetic PDF builder; [upstream](https://www.reportlab.com/) |
| multilingual-e5-small | Embedding weights, downloaded separately; [model card](https://huggingface.co/intfloat/multilingual-e5-small) identifies MIT terms |
| Qwen3.5-9B | Local generation; [original model card](https://huggingface.co/Qwen/Qwen3.5-9B) identifies Apache-2.0 terms |
| LM Studio | Separate local inference runtime; [vendor](https://lmstudio.ai/) |

Generation provenance records `qwen/qwen3.5-9b`, Q4_K_M, context 8192, and the loaded identifier. It does not include an exact GGUF file hash or a quantizer-source license receipt. The original Qwen model card does not establish the provenance of that particular local quantized file. No weights are distributed here; preserve the exact provider's notices and provenance if distributing them later.

No blanket license is added. The repository owner needs to confirm the imported application's source provenance and choose a license for the contributions they have authority to license. A project license would not replace dependency, model, runtime, or document terms.
