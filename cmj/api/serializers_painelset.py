
from rest_framework import serializers
from cmj.painelset.models import Cronometro, CronometroEvent
class CronometroSerializer(serializers.ModelSerializer):
    """Serializer para cronômetros"""
    elapsed_time = serializers.ReadOnlyField()
    remaining_time = serializers.ReadOnlyField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Cronometro
        fields = [
            'id', 'name', 'parent', 'duration', 'state',
            'stop_parent_on_finish', 'reduce_parent_time',
            'created_at', 'started_at', 'paused_at', 'finished_at',
            'elapsed_time', 'remaining_time', 'children_count'
        ]
        read_only_fields = ['started_at', 'paused_at', 'finished_at']

    def get_children_count(self, obj):
        return obj.children.count()

class CronometroEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de cronômetros"""
    class Meta:
        model = CronometroEvent
        fields = ['id', 'cronometro', 'event_type', 'timestamp', 'triggered_by_child']

class CronometroTreeSerializer(serializers.ModelSerializer):
    """Serializer recursivo para árvore de cronômetros"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Cronometro
        fields = [
            'id', 'name', 'state', 'duration',
            'elapsed_time', 'remaining_time',
            'stop_parent_on_finish', 'reduce_parent_time',
            'children'
        ]

    def get_children(self, obj):
        children = obj.get_children()
        return CronometroTreeSerializer(children, many=True).data