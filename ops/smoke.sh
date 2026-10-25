#!/usr/bin/env bash
# End-to-end smoke test against ANY running Financial Statement backend (compose, staging, prod).
# Exercises: health → register → company → prior-year filing → filing → upload →
#            generate → validate (R001/R007) → cash-flow → ratios → AI notes (self-
#            criticism) → audit memo (ReWOO) → chat (ReAct) → submit → review →
#            accept → export → checklist → /metrics (observability).
# Usage: bash ops/smoke.sh [BASE_URL]        (default http://localhost:8000)
set -euo pipefail
BASE="${1:-http://localhost:8000}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP=$(date +%s)
PASS=0; FAIL=0

json_get() { python3 -c "import sys,json; d=json.load(sys.stdin); print(d$1)"; }
check() { # check <label> <expected> <actual>
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ok   $1";
  else FAIL=$((FAIL+1)); echo "  FAIL $1 (expected '$2', got '$3')"; fi
}

echo "== Financial Statement smoke @ $BASE =="

H=$(curl -s "$BASE/healthz" | json_get "['status']")
check "healthz" "ok" "$H"
VER=$(curl -s "$BASE/version" | json_get "['app']")
check "version.app" "Financial Statement" "$VER"

PE="smoke-prep-$STAMP@example.com"; RE="smoke-rev-$STAMP@example.com"; PW="smoke-pass-123"
curl -s -X POST "$BASE/api/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$PE\",\"password\":\"$PW\",\"role\":\"preparer\"}" > /dev/null
curl -s -X POST "$BASE/api/auth/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$RE\",\"password\":\"$PW\",\"role\":\"reviewer\"}" > /dev/null
PT=$(curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$PE\",\"password\":\"$PW\"}" | json_get "['access_token']")
RT=$(curl -s -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$RE\",\"password\":\"$PW\"}" | json_get "['access_token']")
check "preparer login" "true" "$([ -n "$PT" ] && echo true || echo false)"
check "reviewer login" "true" "$([ -n "$RT" ] && echo true || echo false)"
PH="Authorization: Bearer $PT"; RH="Authorization: Bearer $RT"

CID=$(curl -s -X POST "$BASE/api/companies" -H "$PH" -H 'Content-Type: application/json' \
  -d '{"name":"Smoke Co","fiscal_year_end_month":3}' | json_get "['id']")
YEAR=$(date +%Y)
# prior-year filing first: cash-flow (indirect) + YoY anomalies need prior statements
PFID=$(curl -s -X POST "$BASE/api/filings" -H "$PH" -H 'Content-Type: application/json' \
  -d "{\"company_id\":$CID,\"fiscal_year\":$((YEAR-1))}" | json_get "['id']")
curl -s -X POST "$BASE/api/filings/$PFID/trial-balance" -H "$PH" \
  -F "file=@$ROOT/seed/trial_balance_prior_year.csv" > /dev/null
PGEN=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/filings/$PFID/statements/generate" -H "$PH")
check "prior-year statements generated" "201" "$PGEN"
FID=$(curl -s -X POST "$BASE/api/filings" -H "$PH" -H 'Content-Type: application/json' \
  -d "{\"company_id\":$CID,\"fiscal_year\":$YEAR}" | json_get "['id']")
check "company+filing created" "true" "$([ -n "$FID" ] && echo true || echo false)"

TB=$(curl -s -X POST "$BASE/api/filings/$FID/trial-balance" -H "$PH" \
  -F "file=@$ROOT/seed/trial_balance_clean.csv")
TD=$(echo "$TB" | json_get "['total_debit']")
check "upload totals debit" "909000.0" "$TD"

GEN=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/filings/$FID/statements/generate" -H "$PH")
check "generate statements" "201" "$GEN"
NP=$(curl -s "$BASE/api/filings/$FID/statements/pl" -H "$PH" | json_get "['data']['net_profit']")
check "net profit" "60000.0" "$NP"

VAL=$(curl -s -X POST "$BASE/api/filings/$FID/validate" -H "$PH")
R1=$(echo "$VAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(r['passed'] for r in d['results'] if r['rule_id']=='R001'))")
check "R001 balanced" "True" "$R1"
R7=$(echo "$VAL" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(r['passed'] for r in d['results'] if r['rule_id']=='R007'))")
check "R007 cash-flow reconciles" "True" "$R7"

CFO=$(curl -s "$BASE/api/filings/$FID/statements/cf" -H "$PH" | json_get "['data']['operating']['total']")
check "cash-flow operating total" "70000.0" "$CFO"
GAP=$(curl -s "$BASE/api/filings/$FID/statements/cf" -H "$PH" | json_get "['data']['reconciliation_gap']")
check "cash-flow reconciliation gap" "0.0" "$GAP"
CR=$(curl -s "$BASE/api/filings/$FID/ratios" -H "$PH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(r['value'] for r in d if r['key']=='current_ratio'))")
check "current ratio (325k/70k)" "4.6429" "$CR"

NOTE=$(curl -s -X POST "$BASE/api/filings/$FID/notes/draft" -H "$PH" -H 'Content-Type: application/json' \
  -d '{"section":"revenue"}' | python3 -c "import sys,json; print('MOCK NOTE' in json.load(sys.stdin)['draft_text'])")
check "notes draft (self-criticism graph)" "True" "$NOTE"
MEMO=$(curl -s -X POST "$BASE/api/filings/$FID/audit-memo" -H "$PH")
check "audit memo provider" "mock" "$(echo "$MEMO" | json_get "['provider']")"
MM=$(echo "$MEMO" | python3 -c "import sys,json; m=json.load(sys.stdin); print('MOCK AUDIT MEMO' in m['memo'] and len(m['plan'])>=3 and m['observations_count']==len(m['plan']))")
check "audit memo (ReWOO graph)" "True" "$MM"
CHAT=$(curl -s -X POST "$BASE/api/filings/$FID/assistant/chat" -H "$PH" -H 'Content-Type: application/json' \
  -d '{"message":"Summarize this filing."}' | json_get "['provider']")
check "assistant chat (ReAct agent)" "mock" "$CHAT"

SUB=$(curl -s -X POST "$BASE/api/filings/$FID/submit" -H "$PH" | json_get "['status']")
check "submit" "submitted" "$SUB"
SR=$(curl -s -X POST "$BASE/api/filings/$FID/review/transition" -H "$RH" -H 'Content-Type: application/json' \
  -d '{"action":"start_review"}' | json_get "['status']")
check "start_review" "in_review" "$SR"
ACC=$(curl -s -X POST "$BASE/api/filings/$FID/review/transition" -H "$RH" -H 'Content-Type: application/json' \
  -d '{"action":"accept","comment":"smoke"}' | json_get "['status']")
check "accept" "accepted" "$ACC"

PDF=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/filings/$FID/exports/pl.pdf" -H "$PH")
check "export pl.pdf" "200" "$PDF"
XLS=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/filings/$FID/exports/bs.xlsx" -H "$PH")
check "export bs.xlsx" "200" "$XLS"
CL=$(curl -s "$BASE/api/filings/$FID/checklist" -H "$PH" | python3 -c "import sys,json; d=json.load(sys.stdin); print(sum(1 for i in d if i['done']))")
check "checklist items done >= 6" "true" "$([ "$CL" -ge 6 ] && echo true || echo false)"

# --- observability: /metrics endpoint carries business + HTTP metrics -----------
MET=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/metrics")
check "GET /metrics" "200" "$MET"
METRICS=$(curl -s "$BASE/metrics")
check "metric fs_statements_generated_total" "true" \
  "$(echo "$METRICS" | grep -q '^fs_statements_generated_total' && echo true || echo false)"
check "metric fs_workflow_transitions_total" "true" \
  "$(echo "$METRICS" | grep -q '^fs_workflow_transitions_total' && echo true || echo false)"
check "metric http_requests_total" "true" \
  "$(echo "$METRICS" | grep -q '^http_requests_total' && echo true || echo false)"

echo "== smoke: $PASS passed, $FAIL failed =="
[ "$FAIL" -eq 0 ]
