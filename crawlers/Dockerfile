FROM python:3.6.6-slim

ENV PYTHONUNBUFFERED 1

RUN \
    apt-get update && \
    apt-get install gcc build-essential curl -y --no-install-recommends

ADD ./estate_agents/requirements.txt .

RUN \
    pip install -r requirements.txt

COPY ./scrapyd.conf /etc/scrapyd/

WORKDIR /app

ADD scripts/docker-entrypoint.sh .
ADD scripts/wait-for-feedservice.sh .

RUN \
	chmod +x docker-entrypoint.sh && \
	chmod +x wait-for-feedservice.sh

RUN groupadd -g 999 docker && \
    useradd -r -u 999 -g docker docker

RUN chown -R docker:docker .

USER docker

ENTRYPOINT ./docker-entrypoint.sh
