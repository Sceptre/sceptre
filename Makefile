.PHONY: help clean clean-pyc clean-build lint test test-all test-integration install

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - syntatic file validation with pre-commit"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "test-integration - run integration tests"
	@echo "install - install the package to the active Python's site-packages"
	@echo ""
	@ $(MAKE) -C docs help

clean: clean-build clean-pyc clean-test docs-clean

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
	poetry run pre-commit run --all-files

pre:
	poetry install --all-extras -v

test: pre
	poetry run tox

test-integration: pre install
	poetry run behave --junit --junit-directory build/behave

install: clean
	pip install .
