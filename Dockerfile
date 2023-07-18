FROM python:3.10-alpine
RUN apk add --no-cache bash
WORKDIR /app
COPY pyproject.toml README.md CHANGELOG.md ./
COPY sceptre/ ./sceptre
RUN pip install wheel
# Temporarary fix until https://github.com/yaml/pyyaml/issues/601 is resolved
RUN pip install "Cython<3.0" "pyyaml" --no-build-isolation
RUN pip install .
WORKDIR /project
ENTRYPOINT ["sceptre"]
