from pathlib import Path
import os
import sys

import django


PROJECT_ROOT_DIR = Path(os.path.abspath(__file__)).parents[2]

DJANGO_ROOT_DIR = PROJECT_ROOT_DIR / "cmj"
sys.path.append(DJANGO_ROOT_DIR.as_posix())

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "false"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cmj.settings")
django.setup()

from cmj.utils import Manutencao
m = Manutencao()
m.desativa_auto_now()
m.desativa_signals()