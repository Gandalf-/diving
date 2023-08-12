.PHONY: test unittest inttest
test: unittest inttest

unittest:
	python3 -m unittest

inttest:
	bash test/integration.sh


.PHONY: lint shellcheck mypy ruff format
lint: mypy ruff shellcheck

shellcheck:
	shellcheck *.sh */*.sh

mypy:
	mypy .

ruff:
	ruff check --fix .

format:
	black --fast -S *.py */*.py


data/translations.yml: data/taxonomy.yml
	python3 -c 'from util.translator import main; main()'


.PHONY: clean local dev sync
clean:
	bash macos.sh clean

local: data/translations.yml
	bash macos.sh build

dev: data/translations.yml
	bash macos.sh dev

sync:
	bash macos.sh sync
