# Project Setup and Usage Guide

This document describes how to set up the Python environment, configure API keys for LLMs, and run different tasks supported by this project.

---

## 1. Create a Virtual Environment

It is recommended to use a virtual environment to isolate dependencies.

```plaintext
python3 -m venv venv
````

---

## 2. Activate the Virtual Environment

```plaintext
source venv/bin/activate
```

---

## 3. Install Dependencies

Install all required Python packages using `pip`:

```plaintext
pip install -r requirements.txt
```

---

## 4. Configure LLM API Keys

Before running the project, export the required API keys as environment variables.

```plaintext
export DEEPSEEK_API_KEY="YOUR_API_KEY"
export OPENROUTER_API_KEY="YOUR_API_KEY"
```

Make sure the keys are valid and accessible in the current shell session.

---

## 5. Run the Project

The project supports multiple tasks and execution modes. All tasks are launched via `main.py` using command-line arguments.

### 5.1 G24 Task

Run the logic-guided version:

```plaintext
python main.py --task g24 --mode run
```

Run the standard baseline version:

```plaintext
python main.py --task g24 --mode run_standard
```

Extract and validate all expressions from JSONL files under `output/g24`:

```plaintext
python main.py --task g24 --mode extract_expressions
```

---

### 5.2 Sudoku Task

Run the logic-guided version:

```plaintext
python main.py --task sudoku --mode run
```

Run the standard baseline version:

```plaintext
python main.py --task sudoku --mode run_standard
```

Verify all results in JSONL files under `output/sudoku`:

```plaintext
python main.py --task sudoku --mode verify
```

---

### 5.3 Sliding Puzzle Task

Run the logic-guided version:

```plaintext
python main.py --task sliding --mode run
```

Run the standard baseline version:

```plaintext
python main.py --task sliding --mode run_standard
```

---

## 6. Deactivate the Virtual Environment

After finishing your work, you can deactivate the virtual environment:

```plaintext
deactivate
```

---

## Notes

* All experiment outputs are saved under the `output/` directory, organized by task name.
* The `run` mode corresponds to the logic-guided / structured reasoning pipeline.
* The `run_standard` mode corresponds to the baseline or direct prompting pipeline.
* JSONL result files can be post-processed or verified using the provided modes.

---
