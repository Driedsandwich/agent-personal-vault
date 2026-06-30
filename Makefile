.PHONY: test pii release-check clean

test:
	python3 -m unittest discover -s tests

pii:
	python3 scripts/pii_scan.py .

release-check:
	python3 scripts/check_release.py

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	rm -rf build dist *.egg-info
