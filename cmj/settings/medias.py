from decouple import AutoConfig
from easy_thumbnails.conf import Settings as thumbnail_settings
from unipath import Path


config = AutoConfig()

BASE_DIR = Path(__file__).ancestor(2)
PROJECT_DIR = Path(__file__).ancestor(3)

MEDIA_URL = '/media/'
MEDIA_ROOT = PROJECT_DIR.ancestor(1).child("cmj_media").child("media")
MEDIA_PROTECTED_ROOT = PROJECT_DIR.ancestor(
    1).child("cmj_media").child("media_protected")

FILTERS_HELP_TEXT_FILTER = False

IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_JQUERY_URL = None
THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

THUMBNAIL_SOURCE_GENERATORS = (
    'cmj.utils.pil_image',
)

MAX_DOC_UPLOAD_SIZE = 500 * 1024 * 1024  # 200MB
MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
