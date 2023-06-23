tags: *.py */*.py
	ctags -R --fields=+l --languages=python --python-kinds=-i

.PHONY: test
test: unittest inttest

.PHONY: unittest
unittest:
	python3 -m unittest

.PHONY: inttest
inttest:
	bash test_integration.sh

.PHONY: lint
lint:
	mypy .
	ruff check --fix .

.PHONY: format
format:
	black -S *.py */*.py

.PHONY: local
local:
	bash macos.sh build

.PHONY: serve
serve:
	bash macos.sh serve
