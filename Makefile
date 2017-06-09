.PHONY: clean-pyc clean-build docs clean website
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

test:
	python setup.py test

test-all:
	tox

test-integration: install
	behave integration-tests/

coverage:
	coverage run --source sceptre setup.py test
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

coverage-ci:
	coverage run --source sceptre setup.py test
	coverage report -m
	coverage xml

docs:
	rm -f docs/sceptre.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ sceptre
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

website:
	rm -f website/_api/sceptre.rst
	rm -f website/_api/modules.rst
	sphinx-apidoc -o website/_api sceptre
	$(MAKE) -C website/_api clean
	$(MAKE) -C website/_api html
	mkdir -p website/docs/api
	rm -rf website/docs/api/_static
	mkdir -p website/docs/api/_static/
	cp -r website/_api/_build/html/_static website/docs/api/_static/
	rm -f website/docs/api/sceptre.html
	cp website/_api/_build/html/sceptre.html website/docs/api/sceptre.html
	$(MAKE) -C website build-prod

serve-website: website
	$(MAKE) -C website serve

serve-website-prod: website
	$(MAKE) -C website serve-prod

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python setup.py install
