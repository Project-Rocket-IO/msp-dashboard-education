from rest_framework import serializers
from .models import TicketList, TechnicianLabor, ClientWorkTypeRate

class TicketSerializer(serializers.ModelSerializer):
     
    class Meta:
        model = TicketList
        fields = ['create_date', 'identifier']

class TechLaborSerializer(serializers.ModelSerializer):
    hours = serializers.SerializerMethodField()
    day = serializers.SerializerMethodField()
    class Meta:
        model = TechnicianLabor
        fields = ['ticket', 'hours', 'created_at', 'day']

    def get_hours(self, obj):
        return (obj.minutes // 60) + 1
    
    def get_day(self, obj):
        date = obj.created_at
        return date.weekday()

class WorkTypeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientWorkTypeRate
        fields = ['client', 'name', 'rate']

