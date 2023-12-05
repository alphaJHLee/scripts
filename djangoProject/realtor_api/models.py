from django.db import models

# Create your models here.

from django.db import models

# Create your models here.
class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=300)
    cost = models.IntegerField()


class LandRealtorOfficeList(models.Model):
    sigungu = models.CharField(max_length=300, blank=True, null=True)
    city_code = models.CharField(max_length=20)
    last_update_date = models.CharField(max_length=30, blank=True, null=True)
    jurirno = models.CharField(primary_key=True, max_length=200)  # The composite primary key (jurirno, city_code, office_nm, brk_nm) found, that is not supported. The first column is selected.
    office_nm = models.CharField(max_length=200, db_collation='utf8mb4_bin')
    brk_nm = models.CharField(max_length=200)
    status_cd = models.CharField(max_length=5, blank=True, null=True)
    status_nm = models.CharField(max_length=30, blank=True, null=True)
    regist_date = models.CharField(max_length=20, blank=True, null=True)
    tel = models.CharField(max_length=20, blank=True, null=True)
    establish_begin_date = models.CharField(max_length=20, blank=True, null=True)
    establish_end_date = models.CharField(max_length=20, blank=True, null=True)
    direct_yn = models.CharField(max_length=1, blank=True, null=True, db_comment='y or n')

    class Meta:
        managed = False
        db_table = 'land_realtor_office_list'
        unique_together = (('jurirno', 'city_code', 'office_nm', 'brk_nm'),)



class LandRealtorBrokerList(models.Model):
    sigungu = models.CharField(max_length=300, blank=True, null=True)
    city_code = models.CharField(max_length=20)
    last_update_date = models.CharField(max_length=30, blank=True, null=True)
    broker_asort_cd = models.CharField(max_length=5, blank=True, null=True)
    broker_asort_nm = models.CharField(max_length=20, blank=True, null=True)
    certi_no = models.CharField(max_length=50, blank=True, null=True)
    certi_date = models.CharField(max_length=50, blank=True, null=True)
    position_cd = models.CharField(max_length=50, blank=True, null=True)
    position_nm = models.CharField(max_length=50, blank=True, null=True)
    jurirno = models.CharField(max_length=100, blank=True, null=True)
    office_nm = models.CharField(max_length=100, blank=True, null=True)
    brk_nm = models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'land_realtor_broker_list'


class RealtorBrokerOffice(models.Model):
    jurirno = models.CharField(max_length=100, blank=True)
    city_code = models.CharField(max_length=20)
    office_nm = models.CharField(max_length=100, blank=True)
    certi_no = models.CharField(max_length=50, blank=True, null=True)
    brk_nm = models.CharField(max_length=200)
    class Meta:
        managed = False
        unique_together = (('jurirno', 'city_code', 'office_nm'),)


