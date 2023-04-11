FROM python:3.7-alpine
RUN apk add --no-cache bash
WORKDIR /app
COPY sceptre/ ./sceptre
RUN pip install .
WORKDIR /project
ENTRYPOINT ["sceptre"]
