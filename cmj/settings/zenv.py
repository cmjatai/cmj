from decouple import AutoConfig
from unipath import Path

production = Path(__file__).ancestor(4).child("cmj_data").child(".env").exists()

config = AutoConfig(
    search_path=(Path(__file__).ancestor(4).child("cmj_data") if production else None)
)

DEBUG = config("DEBUG", default=False, cast=bool)

BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = Path(__file__).ancestor(3)
