#!/bin/sh
DATABASE_URL="postgresql://cmj:cmj@cmjdb:5432/cmj"

/bin/sh busy-wait.sh $DATABASE_URL



# manage.py migrate --noinput nao funcionava
yes yes | python3 manage.py migrate
#python3 manage.py collectstatic --no-input
# python3 manage.py rebuild_index --noinput &

echo "Criando usuário admin..."

user_created=$(python3 create_admin.py 2>&1)

echo $user_created

cmd=$(echo $user_created | grep 'ADMIN_USER_EXISTS')
user_exists=$?

cmd=$(echo $user_created | grep 'MISSING_ADMIN_PASSWORD')
lack_pwd=$?

if [ $user_exists -eq 0 ]; then
echo "[SUPERUSER CREATION] User admin already exists. Not creating"
fi

if [ $lack_pwd -eq 0 ]; then
echo "[SUPERUSER] Environment variable $ADMIN_PASSWORD for superuser admin was not set. Leaving container"
# return -1
fi

python3 manage.py collectstatic --no-input --clear

#./manage.py runserver 0.0.0.0:8000
/bin/sh gunicorn_docker_start.sh &
/usr/sbin/nginx -g "daemon off;"
