.PHONY: clean local dev prune sitemap sync

local: data/translations.yml
	bash util/macos.sh build

fast: data/translations.yml
	bash util/macos.sh build --fast

dev: data/translations.yml
	bash util/macos.sh dev

sitemap:
	bash util/macos.sh sitemap

sync: sitemap
	bash util/macos.sh sync

serve:
	@serve ~/working/object-publish/diving-web

clean:
	bash util/macos.sh clean

prune:
	bash util/macos.sh prune


data/translations.yml: data/taxonomy.yml
	python3 -c 'from util.translator import main; main()'


.PHONY: lint shellcheck mypy ruff format
lint: shellcheck mypy ruff

shellcheck:
	shellcheck */*.sh

mypy:
	mypy .

ruff:
	ruff check --fix .

format:
	isort --jobs -1 *.py */*.py
	black --fast -S *.py */*.py



.PHONY: test unittest inttest
test: unittest inttest

unittest:
	python3 -m unittest

inttest:
	bash test/integration.sh
