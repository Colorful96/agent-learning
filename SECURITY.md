# Security Policy

## Reporting a Vulnerability

Please do not open a public issue for a suspected security vulnerability. Contact the repository maintainers privately with a description, reproduction steps and the potential impact.

## Local Deployment Notes

- Keep `DEEPSEEK_API_KEY` and other secrets in `.env`, never in source code.
- Set `AGENT_API_TOKEN` before exposing the FastAPI service outside localhost.
- Treat uploaded documents and generated reports as sensitive application data.
- Review allowed paths and tool permissions before deploying the service for other users.
