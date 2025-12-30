SHELL := /bin/bash
RMI ?= all

# Defaults for make pr flags
sync  ?= 0
new   ?= 0
draft ?= 0
b     ?=
base  ?=

.PHONY: help accept compose_up wait seed down pytest_accept unit unitv test lint type typecheck format format-check check ci clean clean-pycache setup-template run-template

help: ## Show available commands
	@echo "Available commands:"
	@echo ""
	@echo "Template Example:"
	@echo "  setup-template    Set up the example template (first time only)"
	@echo "  run-template      Run the svc-infra-template example server"
	@echo ""
	@echo "Testing:"
	@echo "  unit              Run unit tests (quiet)"
	@echo "  unitv             Run unit tests (verbose)"
	@echo "  accept            Run full acceptance tests (with auto-clean)"
	@echo "  test              Run all tests (unit + acceptance)"
	@echo ""
	@echo "Code Quality:"
	@echo "  format            Format code with ruff"
	@echo "  format-check      Check formatting (ruff format --check)"
	@echo "  lint              Lint code with ruff"
	@echo "  type              Type check with mypy"
	@echo "  typecheck         Alias for 'type'"
	@echo "  check             Run lint + type checks"
	@echo "  ci                Run checks + tests"
	@echo "  report            Production readiness analysis report"
	@echo ""
	@echo "Docker Compose (for acceptance):"
	@echo "  compose_up        Start test stack"
	@echo "  wait              Wait for API to be ready"
	@echo "  seed              Seed test data"
	@echo "  down              Tear down test stack"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean             Remove caches, build artifacts, logs"
	@echo "  clean-pycache     Remove only __pycache__ directories"
	@echo ""

compose_up:
	@echo "[accept] Starting test stack..."
	docker compose -f docker-compose.test.yml up -d --remove-orphans --quiet-pull

wait:
	@echo "[accept] Waiting for API to become ready (inside api container)..."
			@ : "Poll the API from inside the running api container to avoid host/port quirks"; \
			end=$$(($(shell date +%s) + 420)); \
		while [ $$(date +%s) -lt $$end ]; do \
			if docker compose -f docker-compose.test.yml exec -T api \
				python -c "import sys,urllib.request; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/ping', timeout=2).status==200 else sys.exit(1)" >/dev/null 2>&1; then \
				echo "[accept] API is ready"; \
				exit 0; \
			fi; \
			sleep 2; \
		done; \
		echo "[accept] Timeout waiting for API"; \
			(docker compose -f docker-compose.test.yml logs --no-color api | tail -n 200 || true); \
		exit 1

seed:
	@echo "[accept] Running CLI migrate/current/downgrade/upgrade (ephemeral sqlite)"
	# Use an ephemeral project root in the container to avoid touching repo files
	# Copy User model, patch env.py to import it early, then run migrations
	docker compose -f docker-compose.test.yml exec -T -e PROJECT_ROOT=/tmp/svc-infra-accept -e SQL_URL=sqlite+aiosqlite:////tmp/svc-infra-accept/accept.db api \
		bash -lc 'rm -rf $$PROJECT_ROOT && mkdir -p $$PROJECT_ROOT && \
		cp /workspace/tests/acceptance/models.py $$PROJECT_ROOT/models.py && \
		python -m svc_infra.cli sql setup-and-migrate --no-with-payments || true && \
		sed -i "3i import sys; sys.path.insert(0, \\\"/tmp/svc-infra-accept\\\"); import models  # Import User model before security models" $$PROJECT_ROOT/migrations/env.py && \
		rm -f $$PROJECT_ROOT/migrations/versions/*.py && \
		python -m svc_infra.cli sql revision --autogenerate -m "initial with user" && \
		python -m svc_infra.cli sql upgrade head && \
		python -m svc_infra.cli sql current && \
		python -m svc_infra.cli sql downgrade -- -1 && \
		python -m svc_infra.cli sql upgrade head'
	@echo "[accept] Seeding acceptance data via CLI (no-op)"
		docker compose -f docker-compose.test.yml exec -T api \
			python -m svc_infra.cli sql seed tests.acceptance._seed:acceptance_seed

pytest_accept:
	@echo "[accept] Running acceptance tests in container..."
	docker compose -f docker-compose.test.yml run --rm tester

accept:
	@echo "[accept] Running full acceptance (with auto-clean)"
	@status=0; \
	$(MAKE) compose_up || status=$$?; \
	if [ $$status -ne 0 ]; then \
		if [ "${CI:-}" = "true" ] || [ "${CI:-}" = "1" ]; then \
			echo "[accept] docker compose failed (CI=true): failing acceptance"; \
		else \
			echo "[accept] docker compose failed; skipping acceptance (set CI=true to enforce)"; \
			status=0; \
		fi; \
	fi; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) wait || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) seed || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) pytest_accept || status=$$?; \
	fi; \
	echo "[accept] Cleaning acceptance stack (containers, volumes, images)"; \
	docker compose -f docker-compose.test.yml down --rmi $(RMI) -v --remove-orphans || true; \
	if [ $$status -eq 0 ]; then \
		echo "[accept] Acceptance complete"; \
	else \
		echo "[accept] Acceptance failed"; \
	fi; \
	exit $$status

down:
	@echo "[accept] Tearing down test stack..."
	docker compose -f docker-compose.test.yml down --rmi $(RMI) -v --remove-orphans

# --- Unit tests ---
unit:
	@echo "[unit] Running unit tests (quiet)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run pytest -q tests/unit; \
	else \
		echo "[unit] Poetry not found; falling back to system pytest"; \
		if command -v pytest >/dev/null 2>&1; then \
			pytest -q tests/unit; \
		else \
			python -m pytest -q tests/unit; \
		fi; \
	fi

unitv:
	@echo "[unit] Running unit tests (verbose)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run pytest -vv tests/unit; \
	else \
		echo "[unit] Poetry not found; falling back to system pytest"; \
		if command -v pytest >/dev/null 2>&1; then \
			pytest -vv tests/unit; \
		else \
			python -m pytest -vv tests/unit; \
		fi; \
	fi

# --- Code Quality ---
format:
	@echo "[format] Formatting with ruff"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run ruff format .; \
	else \
		echo "[format] Poetry not found; falling back to system ruff"; \
		ruff format .; \
	fi

format-check:
	@echo "[format] Checking formatting (ruff format --check)"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run ruff format --check .; \
	else \
		echo "[format] Poetry not found; falling back to system ruff"; \
		ruff format --check .; \
	fi

lint:
	@echo "[lint] Running ruff check"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run ruff check .; \
	else \
		echo "[lint] Poetry not found; falling back to system ruff"; \
		ruff check .; \
	fi

type:
	@echo "[type] Running mypy"
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --no-interaction --only main,dev >/dev/null 2>&1 || true; \
		poetry run mypy src; \
	else \
		echo "[type] Poetry not found; falling back to system mypy"; \
		mypy src; \
	fi

typecheck: type

check: lint type
	@echo "[check] All checks passed"

ci: check test
	@echo "[ci] All checks + tests passed"

# --- Production Readiness Report ---
# Minimum coverage threshold (override with: make report COV_MIN=70)
# Strict mode for CI (override with: make report STRICT=1)
# Report mode: full (default) or ci (skip lint/mypy/pytest, assume CI already ran them)
COV_MIN ?= 60
STRICT ?= 0
REPORT_MODE ?= full

.PHONY: report

report: ## Production readiness gate (CI-friendly with exit codes)
	@set -euo pipefail; \
	echo ""; \
	echo "╔══════════════════════════════════════════════════════════════════════════════╗"; \
	echo "║                    🚀 PRODUCTION READINESS GATE                              ║"; \
	echo "║                           svc-infra                                          ║"; \
	echo "╚══════════════════════════════════════════════════════════════════════════════╝"; \
	echo ""; \
	if [ "$(REPORT_MODE)" = "ci" ]; then \
		if [ "$${CI:-}" != "true" ]; then \
			echo "❌ ERROR: REPORT_MODE=ci requires CI=true environment variable"; \
			echo "   This mode should only be used in GitHub Actions, not locally."; \
			echo "   Run 'make report' instead for full local checks."; \
			exit 1; \
		fi; \
		: "$${LINT_PASSED:?REPORT_MODE=ci requires LINT_PASSED=1 from upstream job}"; \
		: "$${TYPE_PASSED:?REPORT_MODE=ci requires TYPE_PASSED=1 from upstream job}"; \
		: "$${TESTS_PASSED:?REPORT_MODE=ci requires TESTS_PASSED=1 from upstream job}"; \
	fi; \
	VERSION=$$(poetry version -s 2>/dev/null || echo "unknown"); \
	echo "📦 Package Version: $$VERSION"; \
	echo "📋 Coverage Minimum: $(COV_MIN)%"; \
	if [ "$(STRICT)" = "1" ]; then echo "🔒 Strict Mode: ON (fails if score < 9/11)"; fi; \
	if [ "$(REPORT_MODE)" = "ci" ]; then echo "⚡ CI Mode: ON (skipping lint/mypy/pytest)"; fi; \
	echo ""; \
	\
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "🔍 RUNNING ALL CHECKS..."; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo ""; \
	\
	SCORE=0; \
	CRITICAL_FAIL=0; \
	\
	echo "① Linting (ruff)..."; \
	if [ "$(REPORT_MODE)" = "ci" ]; then \
		echo "   ⏭️  SKIP (CI mode - already ran in CI)"; \
		LINT_OK=1; SCORE=$$((SCORE + 1)); \
	else \
		set +e; poetry run ruff check src tests >/dev/null 2>&1; LINT_EXIT=$$?; set -e; \
		if [ "$$LINT_EXIT" -eq 0 ]; then \
			echo "   ✅ PASS (1 pt)"; \
			LINT_OK=1; SCORE=$$((SCORE + 1)); \
		else \
			echo "   ❌ FAIL - linting errors found:"; \
			poetry run ruff check src tests 2>&1 | head -20; \
			LINT_OK=0; \
		fi; \
	fi; \
	echo ""; \
	\
	echo "② Type checking (mypy)..."; \
	if [ "$(REPORT_MODE)" = "ci" ]; then \
		echo "   ⏭️  SKIP (CI mode - already ran in CI)"; \
		TYPE_OK=1; SCORE=$$((SCORE + 1)); \
	else \
		set +e; poetry run mypy src >/dev/null 2>&1; MYPY_EXIT=$$?; set -e; \
		if [ "$$MYPY_EXIT" -eq 0 ]; then \
			echo "   ✅ PASS (1 pt)"; \
			TYPE_OK=1; SCORE=$$((SCORE + 1)); \
		else \
			echo "   ❌ FAIL - type errors found:"; \
			poetry run mypy src 2>&1 | head -20; \
			TYPE_OK=0; \
		fi; \
	fi; \
	echo ""; \
	\
	echo "③ Tests + Coverage (min $(COV_MIN)%)..."; \
	if [ "$(REPORT_MODE)" = "ci" ]; then \
		echo "   ⏭️  SKIP (CI mode - already ran in CI)"; \
		TEST_OK=1; COV_OK=1; SCORE=$$((SCORE + 4)); \
	else \
		set +e; COV_OUTPUT=$$(poetry run pytest --cov=src --cov-report=term-missing -q tests/unit 2>&1); TEST_EXIT=$$?; set -e; \
		COV_PCT=$$(echo "$$COV_OUTPUT" | awk '/^TOTAL/ {for(i=1;i<=NF;i++) if($$i ~ /%$$/) {gsub(/%/,"",$$i); print $$i; exit}}'); \
		if [ -z "$$COV_PCT" ]; then \
			if echo "$$COV_OUTPUT" | grep -qE "unrecognized arguments: --cov|pytest_cov|No module named.*pytest_cov"; then \
				echo "   ❌ FAIL - pytest-cov not installed (poetry add --group dev pytest-cov)"; \
			else \
				echo "   ❌ FAIL - tests failed or no coverage data"; \
				echo "$$COV_OUTPUT" | tail -10; \
			fi; \
			TEST_OK=0; COV_OK=0; CRITICAL_FAIL=1; \
		elif [ "$$TEST_EXIT" -ne 0 ]; then \
			echo "   ❌ FAIL - tests failed"; \
			echo "$$COV_OUTPUT" | tail -10; \
			TEST_OK=0; COV_OK=0; CRITICAL_FAIL=1; \
		elif [ "$$COV_PCT" -lt $(COV_MIN) ]; then \
			echo "   ❌ FAIL - tests passed but $${COV_PCT}% coverage below $(COV_MIN)%"; \
			TEST_OK=1; COV_OK=0; SCORE=$$((SCORE + 2)); CRITICAL_FAIL=1; \
		else \
			echo "   ✅ PASS - $${COV_PCT}% coverage (4 pts: 2 tests + 2 coverage)"; \
			TEST_OK=1; COV_OK=1; SCORE=$$((SCORE + 4)); \
		fi; \
	fi; \
	echo ""; \
	\
	echo "④ Security: Vulnerability scan (pip-audit)..."; \
	if poetry run pip-audit --version >/dev/null 2>&1; then \
		set +e; poetry run pip-audit >/dev/null 2>&1; AUDIT_EXIT=$$?; set -e; \
		if [ "$$AUDIT_EXIT" -eq 0 ]; then \
			echo "   ✅ PASS - no known vulnerabilities (2 pts)"; \
			VULN_OK=1; SCORE=$$((SCORE + 2)); \
		else \
			echo "   ❌ FAIL - vulnerabilities found"; \
			poetry run pip-audit 2>&1 | head -15; \
			VULN_OK=0; CRITICAL_FAIL=1; \
		fi; \
	else \
		if [ "$(STRICT)" = "1" ]; then \
			echo "   ❌ FAIL - pip-audit required in STRICT mode (poetry add --group dev pip-audit)"; \
			VULN_OK=0; CRITICAL_FAIL=1; \
		else \
			echo "   ⚠️  SKIP - pip-audit not installed (0 pts)"; \
			VULN_OK=0; \
		fi; \
	fi; \
	echo ""; \
	\
	echo "⑤ Package build + verification..."; \
	rm -rf dist/; \
	if poetry build -q 2>/dev/null; then \
		if poetry run twine --version >/dev/null 2>&1 && poetry run twine check dist/* >/dev/null 2>&1; then \
			echo "   ✅ PASS - package builds and passes twine check (2 pts)"; \
			BUILD_OK=1; SCORE=$$((SCORE + 2)); \
		elif poetry run python -m zipfile -t dist/*.whl >/dev/null 2>&1; then \
			echo "   ✅ PASS - package builds, wheel is valid (2 pts)"; \
			BUILD_OK=1; SCORE=$$((SCORE + 2)); \
		else \
			echo "   ✅ PASS - package builds (2 pts)"; \
			BUILD_OK=1; SCORE=$$((SCORE + 2)); \
		fi; \
	else \
		echo "   ❌ FAIL - package build failed"; \
		BUILD_OK=0; CRITICAL_FAIL=1; \
	fi; \
	echo ""; \
	\
	echo "⑥ Documentation..."; \
	DOC_SCORE=0; \
	[ -f README.md ] && DOC_SCORE=$$((DOC_SCORE + 1)); \
	[ -f CHANGELOG.md ] && DOC_SCORE=$$((DOC_SCORE + 1)); \
	[ -d docs ] && DOC_SCORE=$$((DOC_SCORE + 1)); \
	if [ "$$DOC_SCORE" -ge 2 ]; then \
		echo "   ✅ PASS - core docs present (1 pt)"; \
		DOCS_OK=1; SCORE=$$((SCORE + 1)); \
	else \
		echo "   ❌ FAIL - missing README.md, CHANGELOG.md, or docs/"; \
		DOCS_OK=0; \
	fi; \
	echo ""; \
	\
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "📋 RESULTS"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo ""; \
	echo "  Component          Weight    Status"; \
	echo "  ─────────────────────────────────────"; \
	[ "$$LINT_OK" = "1" ] && echo "  Linting            1 pt      ✅" || echo "  Linting            1 pt      ❌"; \
	[ "$$TYPE_OK" = "1" ] && echo "  Type checking      1 pt      ✅" || echo "  Type checking      1 pt      ❌"; \
	[ "$$TEST_OK" = "1" ] && echo "  Tests pass         2 pts     ✅" || echo "  Tests pass         2 pts     ❌ CRITICAL"; \
	[ "$$COV_OK" = "1" ] && echo "  Coverage ≥$(COV_MIN)%     2 pts     ✅" || echo "  Coverage ≥$(COV_MIN)%     2 pts     ❌ CRITICAL"; \
	if [ "$$VULN_OK" = "1" ]; then echo "  No vulnerabilities 2 pts     ✅"; \
	elif [ "$(STRICT)" = "1" ]; then echo "  No vulnerabilities 2 pts     ❌ CRITICAL"; \
	else echo "  No vulnerabilities 2 pts     ⚠️  SKIP"; fi; \
	[ "$$BUILD_OK" = "1" ] && echo "  Package builds     2 pts     ✅" || echo "  Package builds     2 pts     ❌ CRITICAL"; \
	[ "$$DOCS_OK" = "1" ] && echo "  Documentation      1 pt      ✅" || echo "  Documentation      1 pt      ❌"; \
	echo "  ─────────────────────────────────────"; \
	echo "  TOTAL              11 pts    $$SCORE"; \
	echo ""; \
	\
	PERCENT=$$((SCORE * 100 / 11)); \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	if [ "$$CRITICAL_FAIL" = "1" ]; then \
		echo ""; \
		echo "  ❌ NOT READY FOR PRODUCTION ($$PERCENT% - $$SCORE/11 pts)"; \
		echo ""; \
		echo "  Critical failures detected. Fix before release:"; \
		[ "$$TEST_OK" = "0" ] && echo "    • Tests must pass"; \
		[ "$$COV_OK" = "0" ] && echo "    • Coverage must be ≥$(COV_MIN)%"; \
		[ "$$VULN_OK" = "0" ] && [ "$(STRICT)" = "1" ] && echo "    • Vulnerabilities must be resolved"; \
		[ "$$BUILD_OK" = "0" ] && echo "    • Package must build successfully"; \
		echo ""; \
		echo "╚══════════════════════════════════════════════════════════════════════════════╝"; \
		exit 1; \
	elif [ "$(STRICT)" = "1" ] && [ "$$SCORE" -lt 9 ]; then \
		echo ""; \
		echo "  ❌ STRICT MODE: Score $$SCORE/11 is below 9/11 threshold"; \
		echo ""; \
		echo "╚══════════════════════════════════════════════════════════════════════════════╝"; \
		exit 1; \
	elif [ "$$SCORE" -ge 9 ]; then \
		echo ""; \
		echo "  ✅ READY FOR PRODUCTION ($$PERCENT% - $$SCORE/11 pts)"; \
		echo ""; \
		echo "╚══════════════════════════════════════════════════════════════════════════════╝"; \
	else \
		echo ""; \
		echo "  ⚠️  NEEDS WORK ($$PERCENT% - $$SCORE/11 pts)"; \
		echo ""; \
		echo "  No critical failures, but score below 9/11."; \
		echo "  Use STRICT=1 to enforce in CI."; \
		echo ""; \
		echo "╚══════════════════════════════════════════════════════════════════════════════╝"; \
	fi

# --- Cleanup helpers ---
clean:
	@echo "[clean] Removing Python caches, build artifacts, and logs"
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info *.log
	@echo "[clean] Cleaning examples directory"
	@cd examples && rm -rf .pytest_cache .mypy_cache .ruff_cache build dist *.egg-info *.log 2>/dev/null || true

# Remove only Python __pycache__ directories (recursive)
clean-pycache:
	@echo "[clean] Removing all __pycache__ directories recursively from project"
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	@echo "[clean] Removing all __pycache__ directories recursively from examples"
	@cd examples && find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

# --- Template example ---
setup-template:
	@echo "[template] Setting up svc-infra-template (install + scaffold + migrations)..."
	@cd examples && $(MAKE) setup

run-template:
	@echo "[template] Installing dependencies for svc-infra-template..."
	@cd examples && poetry install --no-interaction --quiet 2>/dev/null || true
	@echo "[template] Checking if setup has been run..."
	@if [ ! -d "examples/migrations" ]; then \
		echo ""; \
		echo "⚠️  Template not set up yet!"; \
		echo "   Run 'make setup-template' first to scaffold models and initialize the database."; \
		echo ""; \
		exit 1; \
	fi
	@echo "[template] Running svc-infra-template example..."
	@cd examples && env -i HOME="$$HOME" USER="$$USER" TERM="$$TERM" PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin" bash -c 'exec ./run.sh'

# --- Combined test target ---
test:
	@echo "[test] Running unit and acceptance tests"
	@status=0; \
	$(MAKE) unit || status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(MAKE) accept || status=$$?; \
	fi; \
	if [ $$status -eq 0 ]; then \
		echo "[test] All tests passed"; \
	else \
		echo "[test] Tests failed"; \
	fi; \
	exit $$status

# --- Docs Changelog ---
.PHONY: docs-changelog docs docs-serve docs-build

docs-changelog: ## Generate/update docs/CHANGELOG.json for What's New page
	@./scripts/docs-changelog.sh

docs: docs-serve ## Alias for docs-serve

docs-serve: ## Serve documentation locally with live reload
	@echo "[docs] Starting documentation server..."
	poetry run mkdocs serve

docs-build: ## Build documentation for production
	@echo "[docs] Building documentation..."
	poetry run mkdocs build

# --- Git/PR Automation ---
.PHONY: pr commit

# Usage:
#   make pr m="feat: add new feature"        # Create PR from main or update existing PR
#   make pr m="fix: bug" sync=1              # Rebase feature branch on default branch before pushing
#   make pr m="wip" FORCE=1                  # Override conventional commit check
#   make pr m="feat: new" new=1              # Create new PR from feature branch (new branch from HEAD)
#   make pr m="feat: add" b="feat/my-branch" # Use explicit branch name
#   make pr m="feat: wip" draft=1            # Create PR as draft
#   make pr m="fix: hotfix" base=release     # Target a different base branch
pr:
ifndef m
	$(error Usage: make pr m="feat: your commit message")
endif
	@./scripts/pr.sh "$(m)" "$(sync)" "$(new)" "$(b)" "$${FORCE:-0}" "$(draft)" "$(base)"

# Usage: make commit m="feat: add new feature"
# Just commits with proper message (for when you want to batch commits before PR)
commit:
ifndef m
	$(error Usage: make commit m="feat: your commit message")
endif
	@git add -A && git commit -m "$(m)"
