# Build Your Developer Buddy — Student Starter

Open **Assignment.docx** for the complete assignment description. The same text is in **ASSIGNMENT.md**. Start here; the source examples alone are not the assignment.

## What is provided

- `sample_code/`: calculator, average function, and task counter.
- `case_requirements.json`: the expected behavior for each case.
- `tests/`: beginner-friendly supplied checks. Some cases intentionally do not meet all requirements.
- `tools.py`: real `inspect_case` and `run_checks` functions, plus framework-neutral descriptions.
- `report_template.md`: design and evaluation prompts.

You build the Streamlit interface, LLM/controller integration, action loop, trace display, and public deployment. No completed agent is included.

## First run

```text
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q tests/test_calculator.py
```

Read the written requirements before judging a test failure. Some supplied tests are expected to fail; do not weaken them or change the required demo cases to hide failures.

You can also call the tools directly:

```python
from tools import inspect_case, run_checks
print(inspect_case("calculator"))
print(run_checks("calculator"))
```

For your finished app, add `streamlit` and your chosen provider SDK to `requirements.txt`, with versions you have tested. Use `python -m streamlit run app.py` locally. Configure model credentials through local/platform secret settings, never source code. Never ask the instructor for a key when opening your app.

The required cases are `calculator` and `task_counter`. The `average` case is optional. Model access difficulties must be raised early; do not buy a subscription or claim a simulated/replayed answer is a live model response.
