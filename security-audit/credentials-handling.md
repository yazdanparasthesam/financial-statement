# Credentials handling and GitHub CLI authentication

## GitHub CLI

- Prefer `gh auth login --web --hostname github.com --git-protocol https`; do not paste a personal access token into chat, screenshots, shell commands, or project files.
- Use the narrowest credential that supports the task. For a one-repository tracker task, avoid classic PATs carrying organization, enterprise, deletion, package, key-administration, or other unrelated administrative scopes.
- Inspect `gh auth status` locally. Redact account identifiers if needed; never disclose token values. A masked token display is not a credential leak, but excessive scopes should be treated as a least-privilege issue.
- If an over-scoped or unneeded PAT was used, revoke it in GitHub Settings → Developer settings → Personal access tokens, then remove its local credential with `gh auth logout -h github.com` and authenticate again through the browser flow.
- Never store a PAT in `.env`, Git config, project files, shell history, or screenshots. Let `gh` store its browser-flow credential in the OS credential store when available.

## Repository and application secrets

- `.env` stays local and ignored; commit `.env.example` only.
- GitHub Actions, Render, and database credentials belong in their respective secret stores, not in Git or issue bodies.
- If a credential is disclosed, revoke it at the source first, then replace it and document the incident without recording the credential value.
