# Every gate of this repository runs through make — the same on macOS, Linux and Windows (Git Bash or
# any shell with GNU make; uv is the only other tool). `make help` lists the targets.
.PHONY: help sync lint format typecheck imports complexity test test-real examples check build clean

UV ?= uv
# The lowest and a current Python, as CI runs them; `make test PY=3.11` picks one.
PY ?=
UV_RUN = $(UV) run $(if $(PY),--python $(PY),)

help:  ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -e 's/:.*## /\t/'

sync:  ## Install the library and the dev tools into .venv
	$(UV) sync $(if $(PY),--python $(PY),)

lint:  ## Every static check (what CI runs): ruff, format, ty, import layers, complexity
	$(UV_RUN) ruff check --config ruff.toml
	$(UV_RUN) ruff format --check --config ruff.toml
	@$(MAKE) --no-print-directory typecheck imports complexity

typecheck:  ## ty over src, tests and docs/examples
	$(UV_RUN) ty check --config-file ty.toml

imports:  ## The layers of docs/architecture/OVERVIEW.md (import-linter)
	$(UV_RUN) lint-imports --config lint-imports.toml

complexity:  ## Cognitive complexity per function (complexipy, limit 15)
	$(UV_RUN) complexipy src

format:  ## Fix what ruff can fix and format
	$(UV_RUN) ruff check --fix --config ruff.toml
	$(UV_RUN) ruff format --config ruff.toml

test:  ## Unit and contract tests against a fake app over this OS's own door (socket or pipe)
	$(UV_RUN) pytest -q

test-real:  ## Tests against a real `wily serve` (WILY_BIN=/path/to/wily)
	@test -n "$(WILY_BIN)" || { echo 'make test-real WILY_BIN=/path/to/wily' >&2; exit 2; }
	WILY_BIN="$(WILY_BIN)" $(UV_RUN) pytest -q -m real_app

examples:  ## Byte-compile docs/examples (they also go through ruff and ty in lint)
	$(UV_RUN) python -m compileall -q docs/examples

check: lint examples test  ## Everything a change must pass before a push

build:  ## Build the wheel and sdist into dist/
	$(UV) build

clean:  ## Remove caches and build output
	$(UV_RUN) python -c "import shutil; [shutil.rmtree(p, ignore_errors=True) for p in ('dist', '.pytest_cache', '.ruff_cache', '.import_linter_cache')]"
