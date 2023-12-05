from django.urls import include, path
from rest_framework import routers
from . import views #views.py import

router = routers.DefaultRouter() #DefaultRouter를 설정
router.register('Item', views.ItemViewSet) #itemviewset 과 item이라는 router 등록

urlpatterns = [
    path('realtorOffice/', views.realtorapi,name = 'realtorOffice'),
    path('realtorOfficeSpecific/', views.realtorapi_specific11.as_view(),name = 'realtorOfficeSpecific'),
    path('realtorOfficeSpecificCheck/', views.realtorapi_specific_check,name = 'realtorOfficeSpecificCheck')
]

