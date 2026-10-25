# Financial Statement developer entry points — `make help` for the list.
.PHONY: help install test test-unit test-integration test-oncall lint openapi dev-backend dev-frontend \
        frontend-install frontend-test frontend-build compose-up compose-down compose-logs \
        compose-build obs-up obs-down oncall drill drill-sim smoke seed

help:
	@echo "Financial Statement make targets: install test test-unit test-integration test-oncall lint openapi"
	@echo "  dev-backend dev-frontend frontend-install frontend-test frontend-build"
	@echo "  compose-up compose-down compose-logs compose-build obs-up obs-down oncall drill drill-sim smoke seed"

install:
	cd backend && pip install -r requirements-dev.txt

test:
	cd backend && python -m pytest
	python -m pytest oncall-agent/tests -q

test-oncall:
	python -m pytest oncall-agent/tests -q

test-unit:
	cd backend && python -m pytest tests/unit

test-integration:
	cd backend && python -m pytest tests/integration

lint:
	cd backend && ruff check app tests scripts ../oncall-agent

openapi:
	cd backend && python scripts/export_openapi.py

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

frontend-install:
	cd frontend && npm install

frontend-test:
	cd frontend && npm test

frontend-build:
	cd frontend && npm run build

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f --tail=100

compose-build:
	docker compose build

smoke:
	bash ops/smoke.sh ${BASE:-http://localhost:8000}

seed:
	python backend/scripts/seed_demo.py ${BASE:-http://localhost:8000}

obs-up:
	OTEL_ENABLED=true docker compose --profile obs up --build -d

obs-down:
	docker compose --profile obs down

oncall:
	python oncall-agent/agent.py

drill:
	bash ops/alert-drill.sh

drill-sim:
	bash ops/alert-drill.sh --simulate
