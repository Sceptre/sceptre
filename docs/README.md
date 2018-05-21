# Docs

This directory contains the code for Sceptre's [docs](https://sceptre.cloudreach.com).

The docs is written using the [Jekyll](https://jekyllrb.com) framework.

## Ruby

Jekyll depends on Ruby. Documentation on installing Ruby can be found [here](https://www.ruby-lang.org/en/documentation/installation/).

## Usage Summary

For more details see `make help`,

Note: The below assumes you are in the docs directory, if not prefix make commands with `docs-` e.g `make docs-install`

### Install Jekyll

Jekyll and its dependencies can be installed with:

```shell
make install
```

### Build and serve docs locally

The docs can be built with:

```shell
make build-latest
```

To make and serve the docs and watch for changes, run:

```shell
make serve-latest
```

View them at `http://localhost:4000/latest/`
