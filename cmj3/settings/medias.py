from .ambiente import env, BASE_DIR, PROJECT_ROOT

MEDIA_URL = '/media/'
MEDIA_DEV_LOCAL = env.bool('MEDIA_DEV_LOCAL', default=False)

"""
from easy_thumbnails.conf import Settings as thumbnail_settings


MEDIA_ROOT = PROJECT_DIR.ancestor(1).child("cmj_media{}".format(
    '_local' if MEDIA_DEV_LOCAL else ''
)).child("media")

MEDIA_PROTECTED_ROOT = PROJECT_DIR.ancestor(
    1).child("cmj_media{}".format(
        '_local' if MEDIA_DEV_LOCAL else ''
    )).child("media_protected")

FILTERS_HELP_TEXT_FILTER = False

IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_JQUERY_URL = None
THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

THUMBNAIL_SOURCE_GENERATORS = (
    'cmj.utils.pil_image',
)

MAX_DOC_UPLOAD_SIZE = 1512 * 1024 * 1024  # 1512MB
MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
"""