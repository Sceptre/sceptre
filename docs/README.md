# Docs

This directory contains the code for Sceptre's [docs](https://sceptre.cloudreach.com).

The docs is written using the [Jekyll](https://jekyllrb.com) framework.

## Ruby

Jekyll depends on Ruby. Documentation on installing Ruby can be found [here](https://www.ruby-lang.org/en/documentation/installation/).

## Install Jekyll

Jekyll and its dependencies can be installed with:

```shell
make install
```

## Build and serve docs locally

The docs can be built with:

```shell
make docs-latest
```

To makes and serve the docs and watch for changes, run:

```shell
make serve-docs-latest
```

View them at `http://localhost:4000/latest/`
