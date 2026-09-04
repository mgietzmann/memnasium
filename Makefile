# The command list is documented once, in design/Project.md#running-it.

UV   ?= uv
# .mcp.json pins this port, so a Claude Code session's tools only find the server
# on the default. Change PORT and you must change .mcp.json to match.
PORT ?= 8000

DB    := data/memnasium.db
DIST  := app/dist/index.html
SRC   := $(shell find app/src -type f) app/index.html app/vite.config.ts app/package.json

.PHONY: run dev test lint format backup restore types clean

## builds the app if stale, restores the db if missing, serves, opens a browser
run: .venv $(DIST) $(DB)
	@( sleep 1 && open http://127.0.0.1:$(PORT)/ ) &
	$(UV) run uvicorn api.main:app --host 127.0.0.1 --port $(PORT)

## Uvicorn with reload plus the Vite dev server, which proxies /api
dev: .venv app/node_modules $(DB)
	@trap 'kill 0' EXIT INT TERM; \
	$(UV) run uvicorn api.main:app --host 127.0.0.1 --port $(PORT) --reload & \
	cd app && npm run dev

## pytest and the app's tests — design/standards/Tests.md
test: .venv app/node_modules
	$(UV) run pytest
	cd app && npm test

## ruff, mypy, eslint, tsc — design/standards/Code.md
lint: .venv app/node_modules
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy
	cd app && npm run lint && npm run format:check && npx tsc -b --noEmit

format: .venv app/node_modules
	$(UV) run ruff format .
	cd app && npm run format

## dumps the database to data/memnasium.sql, ready to commit
backup: .venv
	$(UV) run python scripts/db.py backup

## rebuilds data/memnasium.db from the dump
restore: .venv
	$(UV) run python scripts/db.py restore

## regenerates the app's types from the Pydantic models
types: .venv app/node_modules
	$(UV) run python scripts/openapi.py openapi.json
	cd app && npm run types

clean:
	rm -rf app/dist openapi.json .pytest_cache .mypy_cache .ruff_cache

.venv: pyproject.toml uv.lock
	$(UV) sync
	@touch .venv

app/node_modules: app/package.json app/package-lock.json
	cd app && npm ci
	@touch app/node_modules

$(DIST): app/node_modules $(SRC)
	cd app && npm run build

$(DB):
	@$(MAKE) restore
