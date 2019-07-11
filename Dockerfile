FROM python:3.6.8-alpine3.9
RUN apk add --no-cache bash
WORKDIR /app
COPY setup.cfg setup.py README.md CHANGELOG.md ./
COPY cli/ ./cli
COPY project_info/ ./project_info
RUN python setup.py install
WORKDIR /project
ENTRYPOINT ["sceptre"]
