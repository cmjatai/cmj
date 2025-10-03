
from rest_framework import serializers
from cmj.painelset.models import Cronometro, CronometroEvent, Evento
from sapl.api.serializers import SaplSerializerMixin

class SecondDurationField(serializers.Field):
    """Campo personalizado para serializar duração em segundos"""

    def to_representation(self, value):
        if value is None:
            return None
        return value.total_seconds()

    def to_internal_value(self, data):
        try:
            seconds = data
            return serializers.timedelta(seconds=seconds)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Duração inválida. Deve ser um número inteiro de segundos.")

class CronometroSerializer(SaplSerializerMixin):
    """Serializer para cronômetros"""
    remaining_time = SecondDurationField()
    elapsed_time = SecondDurationField()
    duration = SecondDurationField()
    last_paused_time = SecondDurationField()
    accumulated_time = SecondDurationField()
    children_count = serializers.SerializerMethodField()

    class Meta(SaplSerializerMixin.Meta):
        model = Cronometro
        fields = '__all__'
        read_only_fields = ['started_at', 'paused_at', 'finished_at']

    def get_children_count(self, obj):
        return obj.children.count()

class CronometroTreeSerializer(CronometroSerializer):
    """Serializer recursivo para árvore de cronômetros"""
    children = serializers.SerializerMethodField()

    class Meta(SaplSerializerMixin.Meta):
        model = Cronometro

    def get_children(self, obj):
        children = obj.get_children()
        return CronometroTreeSerializer(children, many=True).data


class CronometroEventSerializer(SaplSerializerMixin):
    """Serializer para eventos de cronômetros"""
    class Meta:
        model = CronometroEvent
        fields = ['id', 'cronometro', 'event_type', 'timestamp', 'triggered_by_child']

class EventoSerializer(SaplSerializerMixin):
    """Serializer para o modelo Evento"""

    #cronometro = serializers.SerializerMethodField()

    class Meta(SaplSerializerMixin.Meta):
        model = Evento

    """def get_cronometro(self, obj):
        cronometro = obj.cronometro.first()
        if cronometro:
            return CronometroSerializer(cronometro).data
        return None"""