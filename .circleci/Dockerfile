FROM alpine:3.7

RUN apk add --update --no-cache \
    patch \
    git \
    openssh \
    ca-certificates \
    build-base \
    curl \
    bzip2-dev \
    bash \
    python2 \
    python3 \
    py2-pip \
    python2-dev \
    python3-dev \
    libffi-dev \
    ruby \
    ruby-dev \
    ruby-bundler \
    ruby-json \
    readline-dev \
    openssl-dev \
    sqlite-dev \
    zlib-dev

RUN pip install --no-cache-dir virtualenv \
 && pip install --no-cache-dir tox \
 && addgroup -g 3434 circleci \
 && adduser -D -u 3434 -G circleci -s /bin/bash circleci

USER circleci

WORKDIR /home/circleci

ARG PYENV_HOME=/home/circleci/.pyenv

ENV LANG=C.UTF-8 \
    HOME=/home/circleci \
    PATH=$PYENV_HOME/shims:$PYENV_HOME/bin:$PATH

RUN git clone --depth 1 https://github.com/pyenv/pyenv.git $PYENV_HOME \
    && rm -rfv $PYENV_HOME/.git \
    && pyenv install 2.7-dev \
    && pyenv install 3.6-dev \
    && pyenv install 3.7-dev

CMD ["/bin/sh"]
