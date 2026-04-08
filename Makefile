.DEFAULT_GOAL := all

.PHONY: .uv
.uv: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pnpm
.pnpm: ## Check that pnpm is installed
	@pnpm --version || echo 'Please install pnpm: https://pnpm.io/installation'

.PHONY: install
install: .uv ## Install the package and development dependencies
	uv sync --frozen

.PHONY: sync
sync: .uv ## Update local packages and uv.lock
	uv sync

.PHONY: bootstrap-just-bash
bootstrap-just-bash: .pnpm ## Install and build vendored just-bash backend
	cd vendor/just-bash && pnpm install && pnpm build

.PHONY: setup
setup: install bootstrap-just-bash ## Install Python deps and build vendored just-bash backend

.PHONY: format
format: ## Format the code
	uv run ruff format
	uv run ruff check --fix --fix-only

.PHONY: lint
lint: ## Lint the code
	uv run ruff format --check
	uv run ruff check

.PHONY: typecheck-pyright
typecheck-pyright: ## Run static type checking with Pyright
	PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright

.PHONY: typecheck-mypy
typecheck-mypy: ## Run static type checking with Mypy
	uv run mypy

.PHONY: typecheck
typecheck: typecheck-pyright typecheck-mypy ## Run static type checking

.PHONY: test
test: ## Run tests without coverage (fast, for local dev)
	COLUMNS=150 uv run pytest -n auto --dist=loadgroup --durations=10

.PHONY: testcov
testcov: ## Run tests with coverage and generate an HTML report
	COLUMNS=150 uv run coverage run -p -m pytest -n auto --dist=loadgroup --durations=10
	@uv run coverage combine
	@uv run coverage report
	@echo "building coverage html"
	@uv run coverage html

.PHONY: all
all: format lint typecheck testcov ## Run formatting, linting, type checking, and tests with coverage report generation

.PHONY: help
help: ## Show this help (usage: make help)
	@echo "Usage: make [recipe]"
	@echo "Recipes:"
	@awk '/^[a-zA-Z0-9_-]+:.*?##/ { \
		helpMessage = match($$0, /## (.*)/); \
		if (helpMessage) { \
			recipe = $$1; \
			sub(/:/, "", recipe); \
			printf "  \033[36m%-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
		} \
	}' $(MAKEFILE_LIST)
