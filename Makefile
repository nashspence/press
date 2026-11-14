.DEFAULT_GOAL := help
.PHONY: help setup test
PYTHON := mise exec -- uv run --locked python
ASSET_WORKER ?= press-assets
REQUIRE_RETENTION ?= 1

# Load publisher recipes only after setup has installed the locked dependency.
ifneq ($(filter setup,$(MAKECMDGOALS)),)
AFTER_SETUP := $(filter-out setup,$(MAKECMDGOALS))
ifneq ($(strip $(AFTER_SETUP)),)
.PHONY: $(AFTER_SETUP)
$(AFTER_SETUP): setup
	@:
endif
else
CORE_COMMANDS := $(shell $(PYTHON) -m guavajam_core.resources)
ifeq ($(strip $(CORE_COMMANDS)),)
$(error Install the locked dependency with make setup)
endif
include $(CORE_COMMANDS)

help: ## Show publisher commands supplied by the installed core.
	@printf '%s\n\n' 'Usage: make [setup] <target> [NAME=value]'
	@awk -F ':.*## ' '/^[a-z][a-z-]*:.*## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
test: ## Verify this publisher's installed dependency, authoring commands and workflow policy.
	@$(PYTHON) -m unittest discover -s tests
endif

setup: ## Install the pinned tools and locked core dependency.
	mise install
	mise exec -- uv sync --locked
ifneq ($(strip $(AFTER_SETUP)),)
	+$(MAKE) --no-print-directory --file "$(firstword $(MAKEFILE_LIST))" $(AFTER_SETUP)
endif
