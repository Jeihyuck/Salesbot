from django.db import models

# Create your models here.
class Test_Query(models.Model):
    id                  = models.AutoField(primary_key=True)
    case                = models.CharField(verbose_name='Case')
    language            = models.CharField(verbose_name='Language', null=True, blank=True, max_length=2)
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    country             = models.CharField(verbose_name='Country', null=True, blank=True)
    intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
    query               = models.CharField(verbose_name='Query')
    reference_response  = models.TextField(verbose_name='Ref. Response', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)


class Chat_Test(models.Model):
    id                  = models.AutoField(primary_key=True)
    test_query_id       = models.IntegerField(null=True, blank=True)
    case                = models.CharField(verbose_name='Case')
    test_id             = models.CharField(verbose_name='Test ID')
    language            = models.CharField(verbose_name='Language', null=True, blank=True, max_length=2)
    channel             = models.CharField(verbose_name='Channel', null=True, blank=True)
    country             = models.CharField(verbose_name='Country', null=True, blank=True)
    intelligence        = models.CharField(verbose_name='Intelligence', null=True, blank=True)
    query               = models.CharField(verbose_name='Query')
    response            = models.TextField(verbose_name='Response', null=True, blank=True)
    reference_response  = models.TextField(verbose_name='Ref. Response', null=True, blank=True)
    tested              = models.BooleanField(verbose_name='Tested', default=False)
    appraise            = models.CharField(verbose_name='Appraise', null=True, blank=True)
    comment             = models.CharField(verbose_name='Comment', null=True, blank=True)
    created_on          = models.DateTimeField(verbose_name='Create', auto_now_add=True)
    updated_on          = models.DateTimeField(verbose_name='Update', auto_now=True)