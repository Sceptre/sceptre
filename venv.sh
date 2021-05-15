#!/usr/bin/env bash

usage() {
  echo "Usage: source $0"
  echo "A script that sets up a Python Virtualenv"
  exit 1
}

[ "$1" = "-h" ] && usage

version_found=0
for version in $(<.python-version) ; do
  if python --version | grep -q "Python $version" ; then
    ((version_found++))
  fi
done

if ((! version_found)) ; then
  echo "Please use pyenv and install Python $version"
  return
fi

virtualenv venv
. venv/bin/activate

pip install -r requirements/prod.txt
pip install -r requirements/dev.txt
pip install -e .

# vim: set ft=sh:
