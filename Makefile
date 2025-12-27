.PHONY: clean local dev prune sitemap sync

local: data/translations.yml
	bash diving/util/macos.sh build

fast: data/translations.yml
	bash diving/util/macos.sh build --fast

dev: data/translations.yml
	bash diving/util/macos.sh dev

sitemap:
	bash diving/util/macos.sh sitemap

sync: sitemap
	bash diving/util/macos.sh sync

serve:
	@serve ~/working/object-publish/diving-web

clean:
	bash diving/util/macos.sh clean

prune:
	bash diving/util/macos.sh prune


data/translations.yml: data/taxonomy.yml
	python3 -c 'from diving.util.translator import main; main()'


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
	ruff format *.py */*.py


.PHONY: test unittest inttest jstest
test: unittest jstest inttest

unittest:
	python3 -m unittest

jstest:
	jasmine --config=.jasmine.mjs

inttest:
	bash test/integration.sh
