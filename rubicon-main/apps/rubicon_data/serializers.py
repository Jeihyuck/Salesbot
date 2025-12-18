from rest_framework import serializers
from .models import Goods_Base, Goods_Spec_Info, Goods_Spec_Mast

class ModelInputSerializer(serializers.Serializer):
    model = serializers.CharField(max_length=100)

class ProductInputSerializer(serializers.Serializer):
    product_name = serializers.CharField(max_length=100)
    spec_name_kos = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(max_length=100)
        )
    )


class ProductSpecSerializer(serializers.Serializer):
    spec_name_ko = serializers.CharField()
    value = serializers.CharField()

class ProductSerializer(serializers.Serializer):
    model = serializers.CharField()
    product_name = serializers.CharField()
    spec_name_en = serializers.CharField()
    spec_name_ko = serializers.CharField()
    value = serializers.CharField()

class PriceSerializer(serializers.Serializer):
    model = serializers.CharField()
    product_name = serializers.CharField()
    column5 = serializers.CharField()


class FilterSerializer(serializers.Serializer):
    field = serializers.CharField()
    operator = serializers.CharField()
    code = serializers.ListField(child=serializers.CharField())

class InputSerializer(serializers.Serializer):
    view = serializers.CharField()
    field = serializers.ListField(child=serializers.CharField())
    filter = serializers.ListField(child=FilterSerializer())

class ViewInfoInputSerializer(serializers.Serializer):
    view_name = serializers.CharField(required=True)
