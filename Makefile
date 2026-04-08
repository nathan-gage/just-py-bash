.DEFAULT_GOAL := all

TOML_FILES := pyproject.toml just_py_bash/pyproject.toml just_bash_bundled_runtime/pyproject.toml
YAML_FILES := $(wildcard .github/workflows/*.yml)
TAPLO := uv run taplo
YAMLFIX := uv run yamlfix

.PHONY: .uv
.uv: ## Check that uv is installed
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: .pnpm
.pnpm: ## Check that pnpm is installed
	@pnpm --version || echo 'Please install pnpm: https://pnpm.io/installation'

.PHONY: install-python
install-python: .uv ## Install Python development dependencies
	uv sync --frozen

.PHONY: install
install: install-python bootstrap-just-bash build-packaged-runtime ## Install development deps and prepare the packaged just-bash runtime

.PHONY: sync
sync: .uv ## Update local packages and uv.lock
	uv sync

.PHONY: bootstrap-just-bash
bootstrap-just-bash: .pnpm ## Install and build vendored just-bash backend
	cd vendor/just-bash && pnpm install && pnpm build

.PHONY: setup
setup: install ## Backward-compatible alias for install

.PHONY: vendor-bundled-runtime
vendor-bundled-runtime: .uv ## Download and verify the official Node runtime for just_bash_bundled_runtime
	uv run python just_bash_bundled_runtime/tools/vendor_runtime.py

.PHONY: build-packaged-runtime
build-packaged-runtime: bootstrap-just-bash ## Build the packaged just-bash runtime payload used by the Python wrapper
	bash just_py_bash/tools/build_packaged_runtime.sh

.PHONY: build-package
build-package: bootstrap-just-bash ## Build wheel and sdist for just-py-bash
	uv build just_py_bash --out-dir dist

.PHONY: clean
clean: ## Remove generated build artifacts
	rm -rf dist dist-node htmlcov .coverage just_py_bash/src/just_bash/_vendor/just-bash just_bash_bundled_runtime/build just_bash_bundled_runtime/src/just_bash_bundled_runtime.egg-info

.PHONY: build-bundled-runtime
build-bundled-runtime: vendor-bundled-runtime ## Build a wheel for just_bash_bundled_runtime
	uv build just_bash_bundled_runtime --wheel --out-dir dist-node

.PHONY: format-python
format-python: ## Format Python code
	uv run ruff format --preview
	uv run ruff check --fix --fix-only

.PHONY: format-toml
format-toml: ## Format TOML files
	$(TAPLO) format $(TOML_FILES)

.PHONY: format-yaml
format-yaml: ## Format YAML workflow files
	$(YAMLFIX) $(YAML_FILES)

.PHONY: format
format: format-python format-toml format-yaml ## Format the codebase

.PHONY: format-check-python
format-check-python: ## Check Python formatting without modifying files
	uv run ruff format --check --preview

.PHONY: format-check-toml
format-check-toml: ## Check TOML formatting without modifying files
	$(TAPLO) format --check $(TOML_FILES)

.PHONY: format-check-yaml
format-check-yaml: ## Check YAML formatting without modifying files
	$(YAMLFIX) --check $(YAML_FILES)

.PHONY: format-check
format-check: format-check-python format-check-toml format-check-yaml ## Check formatting without modifying files

.PHONY: lint
lint: ## Lint the code
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
test: ## Run the full test suite without coverage
	COLUMNS=150 uv run pytest -n auto --dist=loadgroup --durations=10

.PHONY: test-non-packaging
test-non-packaging: ## Run the non-packaging test suite
	COLUMNS=150 uv run pytest -n auto --dist=loadgroup --durations=10 -m "not packaging"

.PHONY: testcov
testcov: ## Run tests with coverage and generate an HTML report
	COLUMNS=150 uv run coverage run -p -m pytest -n auto --dist=loadgroup --durations=10
	@uv run coverage combine
	@uv run coverage report
	@echo "building coverage html"
	@uv run coverage html

.PHONY: all
all: format lint typecheck test ## Run the standard local development checks

.PHONY: all-ci
all-ci: format-check lint typecheck testcov ## Run the full CI check suite

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
