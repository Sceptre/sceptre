#!/usr/bin/env bash
# Add github
set -e

# Workaround old docker images with incorrect $HOME
# check https://github.com/docker/docker/issues/2968 for details
if [ "${HOME}" = "/" ]
then
    export HOME=$(getent passwd $(id -un) | cut -d: -f6)
fi

mkdir -p ~/.ssh

ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts