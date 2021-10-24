from pathlib import Path
import environ

PROJECT_ROOT = Path(__file__).parent.parent.parent
BASE_DIR = Path(__file__).parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.joinpath('.env'))

DEBUG = env.bool('DEBUG', True)
