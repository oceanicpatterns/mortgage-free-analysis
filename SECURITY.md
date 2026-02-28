# Security Notes

## Data handling

- The app runs locally and does not send input data to external services.
- No authentication, telemetry, or remote storage is implemented.
- CSV export is user-triggered and includes only computed scenario outputs.

## Input safety

- Numeric inputs are bounded in the UI.
- Domain validation rejects non-finite and unrealistic values.
- Validation errors are shown and execution is halted safely.

## Secrets and repo hygiene

- `.streamlit/secrets.toml` and `.env*` files are git-ignored.
- No secret keys are required for this project.
- Review staged files before push.

## Recommended hardening for hosted deployments

- Add authentication if deployed beyond local/private use.
- Add rate limiting and request size limits behind a reverse proxy.
- Pin dependency versions for reproducible builds.
- Run CI security checks (e.g., `pip-audit`) on every pull request.
