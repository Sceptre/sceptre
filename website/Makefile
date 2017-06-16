.PHONY: clean

SHA1 = $(shell git rev-parse --short HEAD)

install:
	bundle install --path vendor

clean:
	rm -rf _site/
	rm -rf .sass-cache/

website:
	bundle exec jekyll build

build:
	bundle exec jekyll build

build-dev:
	bundle exec jekyll build --baseurl /$(SHA1)

serve:
	bundle exec jekyll serve

serve-dev:
	bundle exec jekyll serve --baseurl /$(SHA1)
