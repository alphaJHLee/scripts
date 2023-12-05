from rest_framework import serializers
from .models import Item
from .models import LandRealtorOfficeList,LandRealtorBrokerList,RealtorBrokerOffice
from django.db.models import QuerySet
from rest_framework import serializers

from drf_queryfields import QueryFieldsMixin



class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ("__all__")
        #fields = ('name', 'description', 'cost')


class RealtorOfficeSerializer(QueryFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = LandRealtorOfficeList
        fields = ('jurirno', 'city_code', 'office_nm', 'brk_nm')


class RealtorBrokerSerializer(QueryFieldsMixin,serializers.ModelSerializer):
    class Meta:
        model = LandRealtorOfficeList
        fields = ('jurirno', 'city_code', 'office_nm', 'brk_nm','certi_no')


class RealtorOfficeBrokerDataNew(QueryFieldsMixin,serializers.Serializer):
    class RealtorOfficeBrokerData(QueryFieldsMixin, serializers.Serializer):
        office = RealtorOfficeSerializer(required=False)
        brokers = RealtorBrokerSerializer(many=True)

    realtor_list = RealtorOfficeBrokerData(many=True)


class brokerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandRealtorBrokerList,
        fields = ('certi_no','brk_nm')



class data11(serializers.ModelSerializer):
    broker_lst = brokerSerializer(many=True)
    class Meta:
        model = RealtorBrokerOffice
        fields = ('jurirno','city_code','office_nm','broker_lst')
