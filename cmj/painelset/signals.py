import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch.dispatcher import receiver

from cmj.painelset.signals_sync_refresh import send_signal_for_websocket_sync_refresh


logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], dispatch_uid='syncrefresh_post_signal')
def syncrefresh_post_signal(sender, instance, **kwargs):
    send_signal_for_websocket_sync_refresh(instance, **kwargs)

