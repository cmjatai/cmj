FROM python:3.12.7-bookworm

# TODO:
#    A imagem gerada a partir deste dockerfile
#    não pode ser compartilhada por conter o .env, portanto,
#    uma refatoração seria necessária.

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND noninteractive

ENV RUN0_PACKAGES apt-utils apt-file libpq-dev build-essential pkg-config \
                    libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
                    libcairo2-dev software-properties-common graphviz graphviz-dev \
                    procps nmap git vim bash curl curl jq bash

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $RUN0_PACKAGES

ENV RUN1_PACKAGES python3-dev python3-lxml python3-magic postgresql-client  \
                    python3-psycopg python3-setuptools python3-pip \
                    poppler-utils python3-venv tzdata nodejs nginx
RUN apt-get install -y --no-install-recommends $RUN1_PACKAGES

ENV LIBRE_PACKAGES libreoffice \
                    libreoffice-writer \
                    libreoffice-java-common \
                    libreoffice-core \
                    libreoffice-common \
                    ure \
                    hyphen-pt-br \
                    fonts-opensymbol \
                    fonts-dejavu \
                    fonts-dejavu-core \
                    fonts-dejavu-extra \
                    fonts-droid-fallback \
                    fonts-dustin \
                    fonts-f500 \
                    fonts-fanwood \
                    fonts-freefont-ttf \
                    fonts-lmodern \
                    fonts-lyx \
                    fonts-sil-gentium \
                    fonts-texgyre \
                    fonts-tlwg-purisa \
                    fonts-liberation \
                    fontconfig
RUN apt-get install -y -q $LIBRE_PACKAGES

ENV RUN2_PACKAGES openjdk-17-jdk-headless tesseract-ocr tesseract-ocr-por ghostscript
RUN apt-get install -y --no-install-recommends $RUN2_PACKAGES

RUN mkdir /ghostscript
WORKDIR /ghostscript
RUN wget https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10040/ghostscript-10.04.0.tar.gz
RUN tar vzxfp ghostscript-10.04.0.tar.gz
WORKDIR /ghostscript/ghostscript-10.04.0
RUN ./configure && make && make install

RUN fc-cache -fv && \
    pip3 install --no-cache-dir --upgrade pip setuptools

RUN rm -f /etc/nginx/conf.d/* && \
    rm -f /etc/nginx/sites-enabled/*
    #&& \
    #SUDO_FORCE_REMOVE=yes apt-get purge -y --auto-remove $BUILD_PACKAGES && \
    #apt-get -y autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN adduser --home=/opt/libreoffice --disabled-password --gecos "" --shell=/bin/bash libreoffice
ADD libreoffice_entrypoint.sh /opt/libreoffice/libreoffice_entrypoint.sh
RUN chmod +x /opt/libreoffice/libreoffice_entrypoint.sh

RUN mkdir -p /var/cmjatai/cmj/run
RUN mkdir -p /var/cmjatai/cmj/logs/celery
RUN mkdir -p /var/cmjatai/cmj_data
RUN mkdir -p /var/cmjatai/cmj_media
RUN mkdir -p /var/cmjatai/BD_POSTGRESQL

WORKDIR /var/cmjatai/cmj/

COPY requirements/requirements.txt $HOME
RUN pip install -r /var/cmjatai/cmj/requirements.txt
ADD drfautoapi  /var/cmjatai/cmj/drfautoapi
ADD fonts       /var/cmjatai/cmj/fonts
ADD scripts     /var/cmjatai/cmj/scripts
ADD _frontend   /var/cmjatai/cmj/_frontend
ADD _templates  /var/cmjatai/cmj/_templates
ADD cmj         /var/cmjatai/cmj/cmj
ADD sapl        /var/cmjatai/cmj/sapl
ADD solr        /var/cmjatai/cmj/solr
ADD docker      /var/cmjatai/cmj/docker

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
