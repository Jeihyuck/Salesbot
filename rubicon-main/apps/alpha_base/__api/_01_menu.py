from alpha import __log
from apps.alpha_base.models import Alpha_Menu
from apps.alpha_auth.models import Alpha_User

def get_menu_list(request_dict):
    __log.debug(request_dict)
    user = Alpha_User.objects.get(username=request_dict['user']['username'])

    auth_menu = list(Alpha_Menu.objects.filter(
                alpha_menu_permission__group__in=user.groups.all(),
                alpha_menu_permission__permission=True
            ).distinct().order_by('order').values('id', 'parent_menu__id', 'level', 'name', 'icon', 'url', 'page_title', 'group'))
    
    return True, auth_menu, None, None
