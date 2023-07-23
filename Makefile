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


.PHONY: translations
translations:
	python3 -c 'from util.translator import filter_translations; filter_translations()'

.PHONY: local serve dev
local:
	bash macos.sh build

serve:
	bash macos.sh serve

dev:
	bash macos.sh dev
