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

    from django.contrib.auth import get_user_model
    email = os.environ.get('ADMIN_EMAIL', '')

    if get_user_model().objects.filter(email=email).exists():
        print("[SUPERUSER] User %s already exists."
              " Exiting without change." % email)
        sys.exit('ADMIN_USER_EXISTS')
    else:
        password = get_enviroment_admin_password(email)

        print("[SUPERUSER] Creating superuser...")

        u = get_user_model().objects.create_superuser(
            email=email, password=password)
        u.save()

        print("[SUPERUSER] Done.")

        sys.exit(0)


if __name__ == '__main__':
    django.setup()
    create_superuser()
