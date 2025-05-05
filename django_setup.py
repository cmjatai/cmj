from pathlib import Path
import os
import sys

import django


PROJECT_ROOT_DIR = Path(os.path.abspath(__file__)).parents[1]
DJANGO_ROOT_DIR = PROJECT_ROOT_DIR / "cmj"


def django_setup() -> None:
    """
    Allows to setup Django if it's not already running on a server. Should be called before any Django imports.
    """
    # Add the project base directory to the sys.path
    sys.path.append(DJANGO_ROOT_DIR.as_posix())

    # The DJANGO_SETTINGS_MODULE has to be set to allow us to access django
    # imports
    os.environ['DJANGO_SETTINGS_MODULE'] = 'cmj.settings'

    # This is for setting up django
    django.setup()


django_setup()


