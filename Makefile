.PHONY: test unittest inttest
test: unittest inttest

unittest:
	python3 -m unittest

inttest:
	bash test/integration.sh


.PHONY: lint shellcheck mypy ruff format
lint: shellcheck mypy ruff

shellcheck:
	shellcheck */*.sh

mypy:
	mypy .

ruff:
	ruff check --fix .

format:
	black --fast -S *.py */*.py


data/translations.yml: data/taxonomy.yml
	python3 -c 'from util.translator import main; main()'


.PHONY: clean local dev sitemap sync
clean:
	bash util/macos.sh clean

local: data/translations.yml
	bash util/macos.sh build

dev: data/translations.yml
	bash util/macos.sh dev

sitemap:
	bash util/macos.sh sitemap

sync: sitemap
	bash util/macos.sh sync
