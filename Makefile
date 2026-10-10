.PHONY: check test demo demo-install

PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
VENV_PIP := .venv/bin/pip

check:
	$(PYTHON) scripts/validate_repository.py

demo-install:
	@test -x $(VENV_PYTHON) || $(PYTHON) -m venv .venv
	$(VENV_PIP) install -e ".[demo]"

test: demo-install
	$(PYTHON) scripts/validate_repository.py
	$(VENV_PYTHON) -m unittest discover -s tests -v

demo: demo-install
	$(VENV_PYTHON) -m controlled_agent_runtime.demo
