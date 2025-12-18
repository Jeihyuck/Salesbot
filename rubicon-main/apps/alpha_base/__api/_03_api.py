# from apps.alpha_base.models import Alpha_API
from django.db.models import F, Q
from icecream import ic

# def getAPIList(request_dict):
#     # auth_object = list(Alpha_API.objects.all().order_by('menu').values().annotate(menu=F('menu__menu_name')))
#     return True, None, None, None
# def getAPIList(request_dict):
#     # auth_table = list(Alpha_Table.objects.all().order_by('name').values())
#     api_list = []
#     # Alpha_API.objects.annotate(name=F('table__name'), )
#     # table_data = Alpha_API.objects.only("url", "action", "public").annotate(name=F('table__name'), ).to_dict()
#     # ic(table_data)
#     table_data = list(Alpha_API.objects.filter(object__name__isnull=False).annotate(object_name=F('object__name'), object_type=F('object__type'),).order_by('object_type','object_name').values("id", "url", "action", "no_authentication", "no_access_control", "object_name", "object_type"))
#     # ic(table_data)

#     return True, table_data, [{'itemCount': len(table_data)}], None
#     # return True, None, None, None
