.PHONY: test unittest inttest
test: unittest inttest

unittest:
	python3 -m unittest

inttest:
	bash test/integration.sh


.PHONY: lint mypy ruff format
lint: mypy ruff

mypy:
	mypy .

ruff:
	ruff check --fix .

format:
	black --fast -S *.py */*.py


.PHONY: local
local:
	bash macos.sh build

.PHONY: serve
serve:
	bash macos.sh serve
