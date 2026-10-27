# Troubleshooting episode 001 — Docker Buildx permission denied

**Date:** 2026-10-25  
**Environment:** Linux, Docker Compose v2.27.0, project at `~/Documents/financial-statement`  
**Scope:** local app-only Docker Compose startup.  
**Screenshots:** failure state intentionally not retained in `evidence/`; the successful retry is retained there.

## Symptom

The first non-sudo command:

```bash
docker compose up --build
```

pulled the Postgres image layers, then exited with:

```text
open /home/<user>/.docker/buildx/current: permission denied
```

This indicates the current user could not read Docker Buildx's selected-builder state file. The exact ownership/mode cause has not yet been inspected, so it is intentionally not diagnosed more specifically.

## Recovery used

The owner retried with:

```bash
sudo docker compose up -d
```

That build completed and Compose reported **Running 5/5**, with Postgres and backend healthy and the frontend started. Subsequent `docker compose ps` without `sudo` succeeded, showing all three project services; `/healthz` returned `{"status":"ok"}`, the frontend returned HTTP 200, and the browser displayed the login screen.

## Verification

- `docker compose ps`: `db` healthy, `backend` healthy, `frontend` up.
- `curl -fsS http://localhost:8000/healthz`: `{"status":"ok"}`.
- `curl -I http://localhost:3000`: `HTTP/1.1 200 OK`.
- Browser: `http://localhost:3000/login` displayed the Financial Statement sign-in page.

Successful frames are embedded in `docs/course-submission-runbook.md` Step 2 and indexed in `evidence/README.md`.

## If it happens again

Do not recursively `chmod` or `chown` the Docker config directory. First inspect the specific file and its parent permissions:

```bash
ls -ld "$HOME/.docker" "$HOME/.docker/buildx"
ls -l "$HOME/.docker/buildx/current"
stat "$HOME/.docker/buildx/current"
```

If ownership is wrong, correct only the confirmed affected path, or use the documented system Docker access configuration. Avoid using `sudo` for a mixture of project commands if that creates root-owned files; in this episode the subsequent non-sudo Compose status call succeeded.
