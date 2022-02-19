tags: *.py */*.py
	ctags -R --fields=+l --languages=python --python-kinds=-i

.PHONY: test
test:
	python3 test_sanity.py
	bash test_integration.sh

.PHONY: lint
lint:
	pylint -j 0 --score n *.py **/*.py
	flake8 *.py */*.py

.PHONY: format
format:
	black -l 79 -S *.py */*.py
