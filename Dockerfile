FROM python:3.10-alpine
RUN apk add --no-cache bash
WORKDIR /app
COPY pyproject.toml README.md CHANGELOG.md ./
COPY sceptre/ ./sceptre
RUN pip install wheel
RUN pip install .
WORKDIR /project
ENTRYPOINT ["sceptre"]
