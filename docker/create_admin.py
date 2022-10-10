#!/usr/bin/env python
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")


def get_enviroment_admin_password(username):
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        print(
            "[SUPERUSER] Environment variable $ADMIN_PASSWORD"
            " for user %s was not set. Leaving..." % username)
        sys.exit('MISSING_ADMIN_PASSWORD')
    return password


def create_superuser():
    from cmj.core.models import User

    username = "admin"
    email = os.environ.get('ADMIN_EMAIL', 'admin@jatai.go.leg.br')

    if User.objects.filter(email=email).exists():
        print("[SUPERUSER] User %s already exists."
              " Exiting without change." % username)
        sys.exit('ADMIN_USER_EXISTS')
    else:
        password = get_enviroment_admin_password(username)

        print("[SUPERUSER] Creating superuser...")

        u = User.objects.create_superuser(password=password, email=email)
        u.save()

        print("[SUPERUSER] Done.")

        sys.exit(0)


if __name__ == '__main__':
    django.setup()
    #create_user_cmj()  # must come before create_superuser
    create_superuser()
