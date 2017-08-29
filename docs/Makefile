.PHONY: clean

SHA1 = $(shell git rev-parse --short HEAD)

GIT_TAG = $(shell git describe --abbrev=0 --tags | sed 's/\./-/g')

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

serve-latest: clean
	bundle exec jekyll serve --baseurl /latest

serve-tag: clean
	bundle exec jekyll serve --baseurl /$(GIT_TAG)

serve-dev: clean
	bundle exec jekyll serve --baseurl /dev

serve-commit: clean
	bundle exec jekyll serve --baseurl /$(SHA1)
