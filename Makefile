# memnasium — every command the project has. See design/Project.md.

APP_SRC := $(shell find app/src -type f 2>/dev/null) app/index.html app/package.json app/vite.config.ts
DB      := data/memnasium.db
DUMP    := data/memnasium.sql
DIST    := app/dist/index.html

.PHONY: run dev test lint format backup restore types clean

## builds the app if stale, restores the db if missing, serves, opens a browser
run: .venv $(DIST) $(DB)
	uv run python -m api.run

## Uvicorn with reload plus the Vite dev server, which proxies /api
dev: .venv app/node_modules $(DB)
	uv run uvicorn api.main:app --reload --port 8000 & \
	cd app && npm run dev; \
	kill %1

## pytest and the app's tests
test: .venv app/node_modules
	uv run pytest
	cd app && npm test

## ruff, mypy, eslint, tsc
lint: .venv app/node_modules types
	uv run ruff check api tests
	uv run ruff format --check api tests
	uv run mypy
	cd app && npm run lint

format: .venv app/node_modules
	uv run ruff format api tests
	uv run ruff check --fix api tests
	cd app && npm run format

## dumps the database to data/memnasium.sql, ready to commit
backup: $(DB)
	sqlite3 $(DB) .dump > $(DUMP)

## rebuilds data/memnasium.db from the dump
restore:
	rm -f $(DB)
	$(MAKE) $(DB)

## regenerates the app's types from the API's OpenAPI schema
types: .venv app/node_modules
	uv run python -m api.schema_export > app/src/api/openapi.json
	cd app && npx openapi-typescript src/api/openapi.json -o src/api/schema.d.ts

$(DB): .venv api/schema.sql
	@mkdir -p data/images
	uv run python -m api.restore

$(DIST): app/node_modules $(APP_SRC)
	cd app && npm run build

app/node_modules: app/package.json app/package-lock.json
	cd app && npm ci
	@touch app/node_modules

.venv: pyproject.toml
	uv sync
	@touch .venv

clean:
	rm -rf app/dist app/node_modules .venv
