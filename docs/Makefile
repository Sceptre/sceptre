.PHONY: clean

SHA1 = $(shell git rev-parse --short HEAD)

GIT_TAG = $(shell git describe --abbrev=0 --tags | sed 's/\./-/g')

install:
	bundle install --path vendor

clean:
	rm -rf _site/
	rm -rf .sass-cache/

build-latest:
	bundle exec jekyll build --baseurl /latest

build-tag:
	bundle exec jekyll build --baseurl /$(GIT_TAG)

build-dev:
	bundle exec jekyll build --baseurl /dev

build-commit:
	bundle exec jekyll build --baseurl /$(SHA1)

serve-latest:
	bundle exec jekyll serve --baseurl /latest

serve-tag:
	bundle exec jekyll serve --baseurl /$(GIT_TAG)

serve-dev:
	bundle exec jekyll serve --baseurl /dev

serve-commit:
	bundle exec jekyll serve --baseurl /$(SHA1)
