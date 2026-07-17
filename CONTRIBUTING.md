# Contributing

Thanks for contributing to Research Agent.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and configure a compatible model API before running model-backed tests or demos.

## Before Opening a Pull Request

Run the same checks used by CI:

```powershell
python -m compileall src frontend
python -m pytest tests -q
git diff --check
```

Keep generated files, local databases, uploaded documents, API keys and model caches out of commits. Add or update tests when changing API behavior, workflow routing, retrieval, tools or persistence.

## Pull Requests

Describe the user-facing behavior, list the tests you ran, and call out any new environment variables or external services. Keep changes focused and update the documentation when an entrypoint or configuration changes.
