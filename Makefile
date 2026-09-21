.PHONY: check test

check:
	python3 scripts/validate_repository.py

test:
	python3 -m unittest discover -s tests -v

