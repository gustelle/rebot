FROM gustelle/rep_web_deps

COPY . /app
WORKDIR /app

RUN \
	chmod +x ./scripts/docker-entrypoint.sh && \
	chmod +x ./scripts/wait-for-elastic.sh

RUN groupadd -g 999 docker && \
    useradd -r -u 999 -g docker docker

RUN mkdir -p /app/logs/

RUN chown -R docker:docker .

USER docker

ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
