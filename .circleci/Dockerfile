FROM circleci/python:2.7.13

SHELL ["/bin/bash", "-c"]
USER circleci
ENV RUBY_VERSION 2.4.1
ENV BUNDLER_VERSION 1.14.6

WORKDIR /home/circleci
RUN set -ex \
    \
    && git clone https://github.com/rbenv/rbenv.git $HOME/.rbenv \
    && git clone https://github.com/rbenv/ruby-build.git $HOME/.rbenv/plugins/ruby-build \
    && echo "export PATH=$HOME/.rbenv/bin:$PATH" >> $HOME/.bashrc \
    && echo 'eval "$(rbenv init -)"' >> $HOME/.bashrc

ENV PATH "/home/circleci/.rbenv/shims:/home/circleci/.rbenv/bin:$PATH"
RUN set -ex \
    \
    && rbenv install $RUBY_VERSION \
    && rbenv global $RUBY_VERSION \
    && gem install bundler --version "$BUNDLER_VERSION"
