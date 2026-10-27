# 011 — Render Free service blocked by account card prompt

**Date:** 2026-10-26  
**Area:** Owner-side deployment setup  
**Status:** Resolved by route change; no Render service created  
**Evidence policy:** Failure is documented in prose only; no failure screenshot is retained.

## Context

The Financial Statement deployment was initially planned as a Render API + static frontend with Neon PostgreSQL. The user configured the `fs-dev-api` form for the public `main` branch, backend root, Dockerfile/health check, Frankfurt region, and Free plan. Auto-Deploy was disabled. No service had yet been created.

## Reproduction and observed behavior

1. Select the Render Free plan (`$0/month`) on the service creation form.
2. Submit the “Deploy web service” action.
3. Render presents an “Add Card” payment-method modal instead of creating the service.
4. Canceling returns to the form; retrying reproduces the same prompt.

Render's general documentation says free resources ordinarily do not require payment details, but the actual account flow remained blocked. The user confirmed they do not have a card. No payment information was entered and no Render service was created or deployed.

## Decision

Do not retry the same Render creation flow or ask the user to enter payment details. The user selected the no-card route: FastAPI Cloud for the API, Vercel for the frontend, and Neon for PostgreSQL. Dashboard screenshots are retained only as account/setup-access evidence; they do not prove an app exists or is deployed. The deployment guide and GitHub Actions still need provider-specific adaptation before any claim of live deployment or CD.

## Security / evidence handling

A prior Render environment form displayed a database URL and JWT secret in a screenshot. Do not copy that raw screenshot into repository evidence. Keep only properly redacted evidence; replace the exposed credential values before deployment. This file intentionally contains no credential values, deploy-hook URLs, account email, or payment information.
