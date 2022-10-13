FROM python:3.10-slim-buster

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND noninteractive

ENV BUILD_PACKAGES apt-utils apt-file libpq-dev graphviz-dev build-essential  pkg-config \
                   python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
                   libcairo2-dev software-properties-common python3-setuptools python3-pip

ENV RUN_PACKAGES git graphviz python3-lxml python3-magic postgresql-client python3-psycopg2 \
                 poppler-utils curl jq bash vim python3-venv tzdata nodejs \
                 fontconfig ttf-dejavu python nginx

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $BUILD_PACKAGES $RUN_PACKAGES && \
    fc-cache -fv && \
    pip3 install --no-cache-dir --upgrade pip setuptools

RUN rm -f /etc/nginx/conf.d/* && \
    rm -f /etc/nginx/sites-enabled/*
    #&& \
    #SUDO_FORCE_REMOVE=yes apt-get purge -y --auto-remove $BUILD_PACKAGES && \
    #apt-get -y autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*


RUN mkdir -p /var/cmjatai/cmj
RUN mkdir -p /var/cmjatai/cmj/run
RUN mkdir -p /var/cmjatai/cmj/logs
RUN mkdir -p /var/cmjatai/cmj_data
RUN mkdir -p /var/cmjatai/cmj_media

WORKDIR /var/cmjatai/cmj/

COPY requirements/requirements.txt $HOME
RUN pip install -r /var/cmjatai/cmj/requirements.txt

ADD docker      /var/cmjatai/cmj/docker
ADD drfautoapi  /var/cmjatai/cmj/drfautoapi
ADD fonts       /var/cmjatai/cmj/fonts
ADD _frontend   /var/cmjatai/cmj/_frontend
ADD _templates  /var/cmjatai/cmj/_templates
ADD cmj         /var/cmjatai/cmj/cmj
ADD sapl        /var/cmjatai/cmj/sapl

COPY manage.py $HOME
RUN python3 manage.py collectstatic --noinput --clear --settings=cmj.settings.fake
RUN rm -rf /var/cmjatai/cmj/db.sqlite3

COPY docker/start.sh $HOME
COPY docker/start_gunicorn.sh $HOME
COPY docker/start_daphne.sh $HOME
COPY docker/wait-for-pg.sh $HOME
COPY docker/wait-for-solr.sh $HOME

COPY docker/nginx/cmj_docker.conf /etc/nginx/conf.d/.
COPY docker/nginx/nginx_docker.conf /etc/nginx/nginx.conf


RUN chmod +x /var/cmjatai/cmj/docker/start.sh && \
    chmod +x /var/cmjatai/cmj/docker/start_gunicorn.sh && \
    chmod +x /var/cmjatai/cmj/docker/start_daphne.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-solr.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-pg.sh


# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd --no-create-home nginx

ENV DEBIAN_FRONTEND teletype

EXPOSE 80/tcp 443/tcp

VOLUME ["/var/cmjatai/cmj/data", "/var/cmjatai/cmj_media"]

CMD ["/var/cmjatai/cmj/start.sh"]
