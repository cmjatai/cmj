FROM python:3.10-slim-buster

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND noninteractive

ENV BUILD_PACKAGES apt-utils apt-file libpq-dev graphviz-dev build-essential git pkg-config \
                   python3-dev libxml2-dev libjpeg-dev libssl-dev libffi-dev libxslt1-dev \
                   libcairo2-dev software-properties-common python3-setuptools python3-pip

ENV RUN_PACKAGES graphviz python3-lxml python3-magic postgresql-client python3-psycopg2 \
                 poppler-utils curl jq bash vim python3-venv tzdata nodejs \
                 fontconfig ttf-dejavu python nginx

#https://download.documentfoundation.org/libreoffice/stable/7.4.0/deb/x86_64/LibreOffice_7.4.0_Linux_x86-64_deb.tar.gz

ENV LIBRE_PACKAGES libreoffice \
                    libreoffice-writer \
                    ure \
                    libreoffice-java-common \
                    libreoffice-core \
                    libreoffice-common \
                    openjdk-11-jdk-headless \
                    fonts-opensymbol \
                    hyphen-pt-br \
                    fonts-dejavu \
                    fonts-dejavu-core \
                    fonts-dejavu-extra \
                    fonts-droid-fallback \
                    fonts-dustin \
                    fonts-f500 \
                    fonts-fanwood \
                    fonts-freefont-ttf \
                    fonts-liberation \
                    fonts-lmodern \
                    fonts-lyx \
                    fonts-sil-gentium \
                    fonts-texgyre \
                    fonts-tlwg-purisa

RUN mkdir -p /var/cmjatai/cmj

WORKDIR /var/cmjatai/cmj/

ADD . /var/cmjatai/cmj/

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends $BUILD_PACKAGES $RUN_PACKAGES && \
    fc-cache -fv && \
    apt-get -y -q install ${LIBRE_PACKAGES} && \
    apt-get -y -q remove libreoffice-gnome && \
    pip3 install --no-cache-dir --upgrade pip setuptools && \
    rm -f /etc/nginx/conf.d/* && \
    pip install --no-cache-dir -r /var/cmjatai/cmj/requirements/requirements.txt --upgrade setuptools

    #&& \
    #SUDO_FORCE_REMOVE=yes apt-get purge -y --auto-remove $BUILD_PACKAGES && \
    #apt-get -y autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN adduser --home=/opt/libreoffice --disabled-password --gecos "" --shell=/bin/bash libreoffice
ADD libreoffice_entrypoint.sh /opt/libreoffice/libreoffice_entrypoint.sh
RUN chmod +x /opt/libreoffice/libreoffice_entrypoint.sh

WORKDIR /var/cmjatai/cmj/
ADD . /var/cmjatai/cmj/

COPY docker/start.sh $HOME
COPY docker/solr_cli.py $HOME
COPY docker/wait-for-pg.sh $HOME
COPY docker/wait-for-solr.sh $HOME
COPY docker/create_admin.py $HOME
COPY docker/genkey.py $HOME
COPY docker/gunicorn_start.sh $HOME

COPY docker/config/nginx/cmj.conf /etc/nginx/conf.d
COPY docker/config/nginx/nginx.conf /etc/nginx/nginx.conf
#COPY docker/config/env_dockerfile /var/cmjatai/cmj/cmj/.env

RUN python3 manage.py collectstatic --noinput --clear

# Remove .env(fake) e cmj.db da imagem
#RUN rm -rf /var/cmjatai/cmj/cmj/.env && \
#    rm -rf /var/cmjatai/cmj/cmj.db

RUN chmod +x /var/cmjatai/cmj/start.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-solr.sh && \
    chmod +x /var/cmjatai/cmj/wait-for-pg.sh && \
    ln -sf /dev/stdout /var/log/nginx/access.log && \
    ln -sf /dev/stderr /var/log/nginx/error.log && \
    mkdir /var/log/cmj/ && touch /var/cmjatai/cmj/cmj.log && \
    ln -s /var/cmjatai/cmj/cmj.log /var/log/cmj/cmj.log


# Debian não possui usuário 'nginx' necessário para o Debian
RUN useradd --no-create-home nginx

ENV DEBIAN_FRONTEND teletype

EXPOSE 80/tcp 443/tcp

VOLUME ["/var/cmjatai/cmj/data", "/var/cmjatai/cmj/media"]

CMD ["/var/cmjatai/cmj/start.sh"]
