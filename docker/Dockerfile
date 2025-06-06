FROM leandrojatai/portalcmj:base.0005

# TODO:
#    A imagem gerada a partir deste dockerfile
#    não pode ser compartilhada por conter o .env, portanto,
#    uma refatoração seria necessária.

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /var/cmjatai/cmj/run
RUN mkdir -p /var/cmjatai/cmj/logs/celery
RUN mkdir -p /var/cmjatai/cmj_data
RUN mkdir -p /var/cmjatai/cmj_media
RUN mkdir -p /var/cmjatai/BD_POSTGRESQL

ENV HOME=/var/cmjatai/cmj
WORKDIR ${HOME}

# instalados na imagem base
COPY requirements/requirements.txt $HOME
RUN pip install -r /var/cmjatai/cmj/requirements.txt

COPY requirements/ia-requirements.txt $HOME
RUN pip install -r ia-requirements.txt


ADD drfautoapi  /var/cmjatai/cmj/drfautoapi
ADD fonts       /var/cmjatai/cmj/fonts
ADD scripts     /var/cmjatai/cmj/scripts
ADD solr        /var/cmjatai/cmj/solr
ADD docker      /var/cmjatai/cmj/docker
ADD _frontend   /var/cmjatai/cmj/_frontend
ADD _templates  /var/cmjatai/cmj/_templates
ADD cmj         /var/cmjatai/cmj/cmj
ADD sapl        /var/cmjatai/cmj/sapl

COPY cmj/.env $HOME/cmj/
COPY key_cert.pfx $HOME
COPY manage.py $HOME
RUN python3 manage.py collectstatic --noinput --clear --settings=cmj.settings.fake
RUN rm -rf /var/cmjatai/cmj/db.sqlite3

COPY docker/start.sh $HOME
COPY docker/solr_cli.py $HOME
COPY docker/wait-for-pg.sh $HOME
COPY docker/wait-for-solr.sh $HOME
COPY docker/start_gunicorn.sh $HOME
COPY docker/start_daphne.sh $HOME

COPY docker/nginx/cmj_docker.conf /etc/nginx/conf.d/.
COPY docker/nginx/nginx_docker.conf /etc/nginx/nginx.conf

RUN chmod +x /var/cmjatai/cmj/docker/start.sh && \
    chmod +x /var/cmjatai/cmj/docker/start_gunicorn.sh && \
    chmod +x /var/cmjatai/cmj/docker/start_daphne.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-solr.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-pg.sh

# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd -r -u 1002 --no-create-home -g root nginx

USER nginx

ENV DEBIAN_FRONTEND teletype

EXPOSE 80/tcp 443/tcp

VOLUME ["/var/cmjatai/cmj/data", "/var/cmjatai/cmj_media", "/var/cmjatai/cmj/logs"]

CMD ["/var/cmjatai/cmj/start.sh"]
