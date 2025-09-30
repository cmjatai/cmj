
# timer_app/serializers.py - Serializers para API REST
from rest_framework import serializers
'''
class TimerSerializer(serializers.ModelSerializer):
    """Serializer para cronômetros"""
    elapsed_time = serializers.ReadOnlyField()
    remaining_time = serializers.ReadOnlyField()
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Timer
        fields = [
            'id', 'name', 'parent', 'duration', 'state',
            'stop_parent_on_finish', 'reduce_parent_time',
            'created_at', 'started_at', 'paused_at', 'finished_at',
            'elapsed_time', 'remaining_time', 'children_count'
        ]
        read_only_fields = ['started_at', 'paused_at', 'finished_at']

    def get_children_count(self, obj):
        return obj.children.count()

class TimerEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de cronômetros"""
    class Meta:
        model = TimerEvent
        fields = ['id', 'timer', 'event_type', 'timestamp', 'triggered_by_child']

class TimerTreeSerializer(serializers.ModelSerializer):
    """Serializer recursivo para árvore de cronômetros"""
    children = serializers.SerializerMethodField()

    class Meta:
        model = Timer
        fields = [
            'id', 'name', 'state', 'duration',
            'elapsed_time', 'remaining_time',
            'stop_parent_on_finish', 'reduce_parent_time',
            'children'
        ]

    def get_children(self, obj):
        children = obj.get_children()
        return TimerTreeSerializer(children, many=True).data
'''