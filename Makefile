tags: *.py */*.py
	ctags -R --fields=+l --languages=python --python-kinds=-i

.PHONY: test
test: unittest inttest

.PHONY: unittest
unittest:
	python3 test_sanity.py

.PHONY: inttest
inttest:
	bash test_integration.sh

.PHONY: lint
lint:
	pylint --disable=R0022,E0015 -j 0 --score n *.py **/*.py
	flake8 *.py */*.py
	mypy util/common.py util/database.py util/static.py util/image.py

.PHONY: format
format:
	black -l 79 -S *.py */*.py
