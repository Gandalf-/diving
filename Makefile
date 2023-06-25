.PHONY: test
test: unittest inttest

.PHONY: unittest
unittest:
	python3 -m unittest

.PHONY: inttest
inttest:
	bash test/integration.sh

.PHONY: lint
lint: mypy ruff

.PHONY: mypy
mypy:
	mypy .

.PHONY: ruff
ruff:
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
