FROM python:3.6.7-stretch

#ENV BUILD_PACKAGES postgresql-dev graphviz-dev graphviz build-base git curl pkgconfig \
#                   python3-dev libxml2-dev jpeg-dev libressl-dev libffi-dev libxslt-dev \ 
#                   nodejs npm py3-lxml py3-magic poppler-utils antiword vim openssh-client

ENV BUILD_PACKAGES git curl nginx postgresql-client 

RUN apt -y update 
RUN apt -y upgrade

RUN apt -y install ${BUILD_PACKAGES}

RUN curl -sL https://deb.nodesource.com/setup_9.x | bash -
RUN apt -y install nodejs
RUN npm install npm -g


#RUN apk --update add fontconfig ttf-dejavu && fc-cache -fv

#RUN apt add --no-cache python3 nginx tzdata && \
#    python3 -m ensurepip && \
#    rm -r /usr/lib/python*/ensurepip && \
#    pip3 install --upgrade pip setuptools && \
#    rm -r /root/.cache && \
#    rm -f /etc/nginx/conf.d/*

#RUN mkdir -p /var/cmjatai/cmj && \
#    apk add --update --no-cache $BUILD_PACKAGES


# pip install separado acelera processo de build do docker
RUN pip install gunicorn==19.6.0 \
psycopg2-binary==2.7.4 \
pytz==2018.5 \
libsass==0.11.1 \
unipath==1.1 \
textract==1.5.0 \
whoosh==2.7.4 \
pysolr==3.6.0 \
pyyaml==3.11 \
mysqlclient==1.3.12 \
python-decouple==3.0 \
rtyaml==0.0.3 \
python-dateutil \
WeasyPrint==0.42 \
python-magic==0.4.12 \
dj-database-url==0.4.1


WORKDIR /var/cmjatai/cmj/
ADD . /var/cmjatai/cmj/

RUN pip install -r /var/cmjatai/cmj/requirements/docker-requirements.txt --upgrade setuptools
RUN rm -r /root/.cache

COPY start.sh /var/cmjatai/cmj/
COPY config/nginx/sapl.conf /etc/nginx/conf.d
COPY config/nginx/nginx.conf /etc/nginx/nginx.conf

WORKDIR /var/cmjatai/cmj/cmj-vue
RUN npm run build

WORKDIR /var/cmjatai/cmj/

#RUN pip install -r /var/cmjatai/cmj/requirements/dev-requirements.txt --upgrade setuptools && \
#    rm -r /root/.cache

#COPY config/env_dockerfile /var/cmjatai/cmj/cmj/.env

#RUN python3 manage.py collectstatic --noinput --clear


# Remove .env(fake) e cmj.db da imagem
#RUN rm -rf /var/cmjatai/cmj/cmj/.env && \
#    rm -rf /var/cmjatai/cmj/cmj.db

#RUN chmod +x /var/cmjatai/cmj/start.sh && \
#    ln -sf /dev/stdout /var/log/nginx/access.log && \
#    ln -sf /dev/stderr /var/log/nginx/error.log && \
#    mkdir /var/log/cmj/

VOLUME ["/var/cmjatai/cmj/data", "/var/cmjatai/cmj/media", "/var/cmjatai/cmj/media_protected"]

CMD ["/var/cmjatai/cmj/start.sh"]
