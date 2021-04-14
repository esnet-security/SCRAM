from rest_framework import serializers

from ..models import ActionType, Entry, Route


class ActionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionType
        fields = ['pk', 'name', 'available']


class EntrySerializer(serializers.ModelSerializer):
    route = serializers.IPAddressField()
    actiontype = serializers.CharField(default="1")

    class Meta:
        model = Entry
        fields = '__all__'

    def create(self, validated_data):
        route = validated_data.pop('route')
        actiontype = validated_data.pop('actiontype')
        route_instance, created = Route.objects.get_or_create(route=route)
        try:
            actiontype_instance = ActionType.objects.get(pk=actiontype)
        except:
            actiontype_instance = ActionType.objects.get(name="block")
        entry_instance = Entry.objects.create(**validated_data, route=route_instance, actiontype=actiontype_instance)
        return entry_instance
