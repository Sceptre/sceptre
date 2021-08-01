FROM python:3.7-alpine as base

WORKDIR /app

FROM base as builder

ENV PIP_DISABLE_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.1.7

RUN apk add --no-cache cargo gcc libffi-dev openssl-dev
RUN pip --no-cache-dir install "poetry==${POETRY_VERSION}"
RUN python -m venv /venv

COPY pyproject.toml poetry.lock ./
RUN poetry export -vvv -f requirements.txt | /venv/bin/pip install -r /dev/stdin

COPY . .
RUN poetry build && /venv/bin/pip install dist/*.whl

FROM base as final

RUN apk add --no-cache bash
COPY --from=builder /venv /venv

WORKDIR /project
ENTRYPOINT ["/venv/bin/sceptre"]
