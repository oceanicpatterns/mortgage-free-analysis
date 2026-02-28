# Mortgage Planning Sandbox (Streamlit)

Generic, privacy-safe mortgage planning app designed for public GitHub sharing.

License: MIT (`LICENSE`)

## What changed for GitHub safety

- Removed all personal-looking defaults and replaced them with generic sample values.
- No file/database writes other than optional CSV export initiated by the user.
- No secret keys required.
- Input validation blocks invalid, extreme, or non-finite values.

## Product goals

- Novice-friendly guided flow.
- Clear assumptions and transparent metrics.
- Scenario-based planning, not prediction.
- Testable architecture with separated calculation service from UI.

## Architecture

- `app.py`: Streamlit UI and user guidance.
- `mortgage_free_analysis/models.py`: validated domain models.
- `mortgage_free_analysis/service.py`: pure analysis service (reusable in API/CLI).
- `tests/test_service.py`: strict calculation/validation tests.
- `tests/test_ui_paths.py`: automated UI path tests using Streamlit test harness.

## Core assumptions

- Rate is fixed for each scenario run.
- Overpayment is applied once every 12th month.
- Insurance and recurring fee are annual costs.
- Results are planning estimates only (not financial advice).

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8502
```

Open the local URL shown in terminal.

## Run tests

```bash
pytest -q
```

Security guidance is documented in `SECURITY.md`.

## GitHub onboarding package included

- `LICENSE` (MIT)
- CI workflow: `.github/workflows/ci.yml`
- Contribution guide: `CONTRIBUTING.md`
- PR template: `.github/pull_request_template.md`
- Issue templates: `.github/ISSUE_TEMPLATE/*`

## Novice user journey

1. Use sidebar `Inputs` for property, loan, rate, term, and annual costs.
2. Check KPI cards at top (payment, payoff years, interest, deposit/LTV).
3. Open `Scenario Lab` to inspect rate sensitivity and overpayment heatmap.
4. Open `Compare Plans` for side-by-side strategy decisions.
5. Use `Cashflow Tables` and CSV export for records.

## UX & DQ audit checklist embedded in app

- Guided quick-start text on page.
- Validation errors shown inline with clear fixes.
- All tabs available without hidden navigation.
- Defensive bounds on all numeric inputs.
- Labels avoid country-specific assumptions where possible.

## Secure GitHub upload checklist

- Ensure `.venv/`, caches, and editor files are ignored.
- Do not commit `.streamlit/secrets.toml`.
- Review staged files before push:

```bash
git status
git diff --staged
```

- Optional: add branch protection and CI for `pytest` before merging.
