.PHONY: clean

SHA1 = $(shell git rev-parse --short HEAD)

GIT_TAG = $(shell git describe --abbrev=0 --tags | sed 's/\./-/g')

help:
	@echo "docs Makefile (if called from parent directory must be prefixed with docs)"
	@echo "e.g docs-serve-latest"
	@echo ""
	@echo "install - install jekyll and it's dependencies"
	@echo "build-{latest,dev,tag,commit} - build the latest docs using a baseurl of {latest,dev,tag,commit}"
	@echo "serve-{latest,dev,tag,commit} - build and locally serve the latest docs on a baseurl of localhost:400/{latest,dev,tag,commit}"
	@echo ""
	@echo "baseurls:"
	@echo "- latest - static"
	@echo "- dev -static"
	@echo "- tag - dynamic based on the current git tag"
	@echo "- commit - dynamic based on the current git sha1"
	@echo ""
	@echo "note: There is also a makefile in docs/_api (cd to docs/api and run make help for more info)"

install:
	bundle install --path vendor

clean: clean-api
	rm -rf _site/
	rm -rf .sass-cache/

clean-api:
	rm -f _api/sceptre.rst
	rm -f _api/modules.rst
	sphinx-apidoc -o _api ../sceptre
	$(MAKE) -C _api clean

build-api: clean-api
	$(MAKE) -C _api html
	rm -rf docs/api/
	cp -r _api/_build/html docs/
	mv docs/html docs/api

build-latest: clean build-api
	bundle exec jekyll build --baseurl /latest

build-tag: clean build-api
	bundle exec jekyll build --baseurl /$(GIT_TAG)

build-dev: clean build-api
	bundle exec jekyll build --baseurl /dev

build-commit: clean build-api
	bundle exec jekyll build --baseurl /$(SHA1)

serve-latest: clean build-latest
	bundle exec jekyll serve --baseurl /latest

serve-tag: clean build-tag
	bundle exec jekyll serve --baseurl /$(GIT_TAG)

serve-dev: clean build-dev
	bundle exec jekyll serve --baseurl /dev

serve-commit: clean build-commit
	bundle exec jekyll serve --baseurl /$(SHA1)
