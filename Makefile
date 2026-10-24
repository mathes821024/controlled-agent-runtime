.PHONY: help check test demo demo-install agent-example

PYTHON ?= python3
VENV_PYTHON := .venv/bin/python
VENV_PIP := .venv/bin/pip
CAR_BASE_URL ?= http://127.0.0.1:8000
SCENARIO ?= safe_auto

help:
	@echo "make check          contract validation (no extra deps, no network)"
	@echo "make test           check + unit tests (installs .[demo] into .venv)"
	@echo "make demo           Human Acceptance UI on 127.0.0.1:8000 (no LLM)"
	@echo "make demo-install   create .venv and install FastAPI extras"
	@echo "make agent-example  stub LangGraph → POST /api/agent/propose (optional .[agent])"
	@echo "See docs/ops/2gb-vps-quickstart.md for a 2GB VPS path."

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

agent-example:
	@test -x $(VENV_PYTHON) || $(PYTHON) -m venv .venv
	$(VENV_PIP) install -e ".[demo,agent]"
	CAR_BASE_URL=$(CAR_BASE_URL) PYTHONPATH=examples $(VENV_PYTHON) -m agent_graph --scenario $(SCENARIO)

