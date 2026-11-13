.DEFAULT_GOAL := help
.PHONY: help setup test
PYTHON := mise exec -- uv run --locked python
ASSET_WORKER ?= press-assets

# Bootstrap does not need an installed package. Every publishing command does.
ifeq ($(filter setup,$(MAKECMDGOALS)),)
CORE_COMMANDS := $(shell $(PYTHON) -m guavajam_core.resources)
ifeq ($(strip $(CORE_COMMANDS)),)
$(error Install the locked dependency with make setup)
endif
include $(CORE_COMMANDS)
endif

help: ## Show publisher commands supplied by the installed core.
	@awk -F ':.*## ' '/^[a-z][a-z-]*:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
setup: ## Install the pinned tools and locked core dependency.
	mise install
	mise exec -- uv sync --locked
test: ## Verify this publisher's installed dependency, authoring commands and workflow policy.
	@$(PYTHON) -m unittest discover -s tests
