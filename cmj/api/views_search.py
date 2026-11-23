import logging

from django.apps.registry import apps
from rest_framework.exceptions import PermissionDenied

from cmj.search.models import ChatMessage, ChatSession
from cmj.search.services.s_chat import ChatHistoricoService
from drfautoapi.drfautoapi import ApiViewSetConstrutor, customize

logger = logging.getLogger(__name__)

ApiViewSetConstrutor.build_class([apps.get_app_config("search")])


@customize(ChatSession)
class ChatSessionViewSet:

    def get_queryset(self):
        qs = ChatHistoricoService.sessoes_do_usuario(
            self.request.user, super().get_queryset()
        )
        self.queryset = qs
        return qs


@customize(ChatMessage)
class ChatMessageViewSet:

    def get_queryset(self):
        return ChatHistoricoService.mensagens_do_usuario(
            self.request.user, super().get_queryset()
        )

    def _confere_sessao(self, serializer):
        sessao = serializer.validated_data.get("chat")
        if sessao and not ChatHistoricoService.e_dono_da_sessao(
            self.request.user, sessao
        ):
            raise PermissionDenied()

    def perform_create(self, serializer):
        self._confere_sessao(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._confere_sessao(serializer)
        serializer.save()
