.PHONY: clean-pyc clean-build docs clean docs
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "test-integration - run integration tests"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "coverage-ci - check code coverage and generate cobertura report"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -fr .cache/
	rm -f .coverage
	rm -fr htmlcov/
	rm -f test-results.xml

lint:
	flake8 sceptre tests
	python setup.py check -r -s -m

test:
	pytest

test-all:
	tox

test-integration: install
	behave integration-tests/

coverage-ci:
	coverage erase
	coverage run --source sceptre -m pytest
	coverage html

coverage: coverage-ci
	coverage report --show-missing
	$(BROWSER) htmlcov/index.html

docs:
	rm -f docs/sceptre.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ sceptre
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

docs-api:
	rm -f docs/_api/sceptre.rst
	rm -f docs/_api/modules.rst
	sphinx-apidoc -o docs/_api sceptre
	$(MAKE) -C docs/_api clean
	$(MAKE) -C docs/_api html
	rm -rf docs/docs/api/
	cp -r docs/_api/_build/html docs/docs/
	mv docs/docs/html docs/docs/api

docs-latest: docs-api
	$(MAKE) -C docs build-latest

docs-tag: docs-api
	$(MAKE) -C docs build-tag

docs-dev: docs-api
	$(MAKE) -C docs build-dev

docs-commit: docs-api
	$(MAKE) -C docs build-commit

serve-docs-latest: docs-latest
	$(MAKE) -C docs serve-latest

serve-docs-tag: docs-tag
	$(MAKE) -C docs serve-tag

serve-docs-dev: docs-dev
	$(MAKE) -C docs serve-dev

serve-docs-commit: docs-commit
	$(MAKE) -C docs serve-commit

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	pip install .

install-dev: clean
	pip install -r requirements.txt
	pip install -e .
	@echo "To install the documentation dependencies, run:\ncd docs\nmake install"
