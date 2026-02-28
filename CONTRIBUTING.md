# Contributing

Thanks for contributing.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run app.py --server.port 8502
```

## Run tests

```bash
pytest -q
```

## Contribution standards

- Keep the app privacy-safe: never add personal user data defaults.
- Preserve input validation and novice-friendly guidance in the UI.
- Add or update tests for behavior changes.
- Keep changes focused and document assumptions in PR descriptions.

## Pull request checklist

- [ ] Tests pass locally.
- [ ] New behavior has test coverage.
- [ ] README updated if UX or setup changed.
- [ ] No secrets or local environment files included.
