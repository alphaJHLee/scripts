from django.shortcuts import render

from django.db.models import F
from django.http import JsonResponse
from rest_framework import viewsets,status
from .serializers import ItemSerializer,RealtorOfficeSerializer,RealtorOfficeBrokerDataNew,data11
from .models import Item,LandRealtorOfficeList,LandRealtorBrokerList,RealtorBrokerOffice
import json
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from  .jwt_validation import jwt_validation
from django.db import connection
import pandas as pd


# Create your views here.
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer





@api_view(['POST'])
def realtorapi(request):
    datas = LandRealtorOfficeList.objects.all()
    serializer = RealtorOfficeSerializer(datas, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def realtorapi_setdata(request):
    datas = LandRealtorOfficeList.objects.all()
    serializer = RealtorOfficeSerializer(datas, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def realtorapi_specific(request):
    reqData = json.loads(request.body)
    datas = LandRealtorOfficeList.objects.filter(jurirno = str(reqData['jurirno']),
                                                 city_code = str(reqData['city_code']),
                                                 office_nm = str(reqData['office_nm']))
    serializer = RealtorOfficeSerializer(datas, many=True)
    return Response(serializer.data)

#LandRealtorOfficeList,LandRealtorBrokerList

class realtorapi_specific11(APIView):

    def post(self,request):
        #get_token = request.META['HTTP_AUTHORIZATION']
        #jwt_validation(get_token)
        reqData = json.loads(request.body)
        data = LandRealtorOfficeList.objects.filter(jurirno = reqData['jurirno'],
                                                    city_code = F('LandRealtorBrokerList__city_code'),
                                                    office_nm = F('LandRealtorBrokerList__office_nm')
                                                    ).values('jurirno', 'office_nm', 'city_code', 'LandRealtorBrokerList__broker_nm',
                                                             'LandRealtorBrokerList__certi_no')
        data = RealtorOfficeBrokerDataNew(data)
        return JsonResponse({'data': data.data})




class realtorapi_specific_check(APIView):

    def post(self,request):
        get_token = request.META['HTTP_AUTHORIZATION']
        try:
            jwt_validation(get_token)
        except Exception as e:
            return Response({'code': 404, 'error': 'invalid token error'})
        else:
            reqData = json.loads(request.body)
            with connection.cursor() as cursor:
                cursor.execute('''select A.jurirno,A.city_code,A.office_nm,B.certi_no,B.brk_nm from 
            office_list as A left join broker_list as B on A.jurirno=B.jurirno and A.office_nm = B.office_nm and 
            A.city_code = B.city_code 
            where A.jurirno = \"%s\" and A.city_code = \"%s\" and A.office_nm = \"%s\"''' % (
                    reqData['jurirno'], reqData['city_code'], reqData['office_nm']))
                row = cursor.fetchall()
                column = [col[0] for col in cursor.description]
            if len(row) == 0:
                return Response({'code': 200, 'success': False})
            else:
                return Response({'code': 200, 'success': True})



