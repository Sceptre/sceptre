FROM python:3.9-alpine
RUN apk add --no-cache bash
WORKDIR /app
COPY setup.cfg setup.py README.md CHANGELOG.md ./
COPY sceptre/ ./sceptre
RUN python setup.py install
RUN pip install .
WORKDIR /project
ENTRYPOINT ["sceptre"]
