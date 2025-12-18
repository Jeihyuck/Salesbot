import json

from rest_framework.renderers import JSONRenderer
from apps.alpha_base.models import Alpha_Table_Field
from apps.alpha_base.serializers import Alpha_Table_Field_Table_Header_Serializer


def get_table_header(request_dict):
    table_id = request_dict['query']['id']
    queryset = Alpha_Table_Field.objects.filter(table_id = table_id).all().order_by('field_seq')
        
    serializer = Alpha_Table_Field_Table_Header_Serializer(queryset, many=True)
    json_result = JSONRenderer().render(serializer.data)
    dict_result = json.loads(json_result)
    
    header = []
    
    for header_item in dict_result:         
        if header_item['hide'] == False:
            header.append(header_item)
        header_item['class'] = header_item.pop('style_class', 'accent white--text')
    return True, header, None, None


