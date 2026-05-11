# Jupyter notebooks — analysis & visualization

This directory contains exploratory notebooks for MindLayer.

## `rag_analysis.ipynb`

Loads the latest offline evaluation report and visualizes:

1. Per-category summary metrics
2. RAGAS-style metrics (when `--enable-ragas` was used)
3. Latency / cost estimates across LLM models
4. Real spend by agent (when cost data is available)

### Running

```bash
# 1. Activate venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. (Re)generate the eval report
.venv/Scripts/python -m eval.run_eval --mode offline --enable-ragas \
    --output-dir eval/results

# 3. Start Jupyter
.venv/Scripts/jupyter lab
# or
.venv/Scripts/jupyter notebook
```

Then open `rag_analysis.ipynb`.

### Requirements

Already in `requirements-dev.txt`:
- `jupyter`
- `pandas`
- `matplotlib`
- `seaborn`
