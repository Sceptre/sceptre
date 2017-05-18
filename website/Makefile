.PHONY: clean

install:
	bundle install --path vendor

clean:
	rm -rf _site/
	rm -rf .sass-cache/

website:
	bundle exec jekyll build

serve:
	bundle exec jekyll serve
