import logging

from django.apps.registry import apps

from cmj.search.models import ChatSession
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class(
    [
        apps.get_app_config('search')
    ]
)

@customize(ChatSession)
class ChatSessionViewSet:

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(user=self.request.user)
        self.queryset = qs
        return qs
