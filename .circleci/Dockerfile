FROM library/alpine:3.6

RUN apk add --update \
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
    libffi-dev \
    ruby \
    ruby-dev \
    ruby-bundler \
    ruby-json

RUN pip install virtualenv \
 && pip install tox \
 && addgroup -g 3434 circleci \
 && adduser -D -u 3434 -G circleci -s /bin/bash circleci

USER circleci
WORKDIR /home/circleci

ENV LANG=C.UTF-8 \
    HOME=/home/circleci

CMD ["/bin/sh"]
