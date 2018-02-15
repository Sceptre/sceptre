.PHONY: clean

SHA1 = $(shell git rev-parse --short HEAD)

GIT_TAG = $(shell git describe --abbrev=0 --tags | sed 's/\./-/g')

help:
	@echo "docs Makefile (if called from parent directory must be prefixed with docs)"
	@echo "e.g docs-serve-latest"
	@echo ""
	@echo "install - install jekyll and it's dependencies"
	@echo "build-(X) - build the latest docs version of the docs and store it in (X)"
	@echo "serve-(X) - build and serve using a baseurl with (X)"
	@echo ""
	@echo "Where (X) can be:"
	@echo " latest"
	@echo " dev"
	@echo " tag - based on the current git tag"
	@echo " sha1 - based on the current git sha1"
	@echo ""
	@echo "note: There is also a makefile in docs/_api (cd to docs/api and run make help for more info)"

install:
	bundle install --path vendor

clean:
	rm -rf _site/
	rm -rf .sass-cache/

build-latest: clean
	bundle exec jekyll build --baseurl /latest

build-tag: clean
	bundle exec jekyll build --baseurl /$(GIT_TAG)

build-dev: clean
	bundle exec jekyll build --baseurl /dev

build-commit: clean
	bundle exec jekyll build --baseurl /$(SHA1)

serve-latest: clean build-latest
	bundle exec jekyll serve --baseurl /latest

serve-tag: clean build-tag
	bundle exec jekyll serve --baseurl /$(GIT_TAG)

serve-dev: clean build-dev
	bundle exec jekyll serve --baseurl /dev

serve-commit: clean build-commit
	bundle exec jekyll serve --baseurl /$(SHA1)
