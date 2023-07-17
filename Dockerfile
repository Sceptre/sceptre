FROM python:3.10
RUN apt-get install bash
WORKDIR /app
COPY pyproject.toml README.md CHANGELOG.md ./
COPY sceptre/ ./sceptre
RUN pip install .
WORKDIR /project
ENTRYPOINT ["sceptre"]
