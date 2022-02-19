tags: *.py
	ctags -R --fields=+l --languages=python --python-kinds=-i

.PHONY: test
test:
	python3 test_sanity.py

.PHONY: lint
lint:
	pylint **/*.py
	flake8 **/*.py
