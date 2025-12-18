from rest_framework import serializers
from .models import Alpha_Table_Field

class Alpha_Table_Field_Table_Header_Serializer(serializers.ModelSerializer):
    class Meta:
        model = Alpha_Table_Field
        fields = ['field_seq', 'hide', 'title', 'align', 'width', 'sortable', 'key', 'style_class']